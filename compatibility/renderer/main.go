// Docker compatibility renderer: pinned Goldmark/Chroma and explicit Docker hooks.
// No Hugo runtime, generic template engine, mounts engine or shortcode evaluator.
package main

import (
	"bufio"
	"bytes"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	stdhtml "html"
	"net/url"
	"os"
	"path"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/alecthomas/chroma/v2"
	ch "github.com/alecthomas/chroma/v2/formatters/html"
	"github.com/alecthomas/chroma/v2/lexers"
	"github.com/alecthomas/chroma/v2/styles"
	"github.com/bep/goat"
	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/ast"
	"github.com/yuin/goldmark/extension"
	ea "github.com/yuin/goldmark/extension/ast"
	"github.com/yuin/goldmark/parser"
	"github.com/yuin/goldmark/renderer"
	gh "github.com/yuin/goldmark/renderer/html"
	"github.com/yuin/goldmark/text"
	"github.com/yuin/goldmark/util"
)

type Request struct {
	Markdown, Route, Source string
	Index                   bool
	LegacyAnchors           map[string]string
}
type Metrics struct {
	MarkdownParseNS, MarkdownRenderNS, HookNS, ChromaNS int64
	Hooks                                               map[string]int
}
type Response struct {
	HTML    string
	Metrics Metrics
	Error   string
	Fences  []string `json:",omitempty"`
}
type Hooks struct {
	request Request
	refs    map[string]string
	icons   map[string]string
	metrics Metrics
	alerts  map[ast.Node]string
}

func esc(s string) string { return stdhtml.EscapeString(s) }
func attr(n ast.Node, key string) string {
	v, ok := n.AttributeString(key)
	if !ok {
		return ""
	}
	if b, ok := v.([]byte); ok {
		return string(b)
	}
	return fmt.Sprint(v)
}
func (h *Hooks) RegisterFuncs(r renderer.NodeRendererFuncRegisterer) {
	for kind, name := range map[ast.NodeKind]string{ast.KindHeading: "heading", ast.KindLink: "link", ast.KindAutoLink: "link", ast.KindImage: "image", ast.KindFencedCodeBlock: "codeblock", ast.KindBlockquote: "blockquote", ea.KindTable: "table", ea.KindTableHeader: "table", ea.KindTableRow: "table", ea.KindTableCell: "table"} {
		label := name
		r.Register(kind, func(w util.BufWriter, source []byte, n ast.Node, enter bool) (ast.WalkStatus, error) {
			before := time.Now()
			chromaBefore := h.metrics.ChromaNS
			result, err := h.render(w, source, n, enter)
			h.metrics.HookNS += time.Since(before).Nanoseconds() - (h.metrics.ChromaNS - chromaBefore)
			if enter {
				h.metrics.Hooks[label]++
			}
			return result, err
		})
	}
}
func (h *Hooks) resolve(destination string) (string, error) {
	u, err := url.Parse(destination)
	if err != nil {
		return "", err
	}
	if u.IsAbs() || strings.HasPrefix(destination, "//") {
		return destination, nil
	}
	if strings.HasPrefix(destination, "/") && !strings.HasSuffix(u.Path, ".md") {
		return destination, nil
	}
	if u.Path == "" {
		return destination, nil
	}
	candidates := []string{strings.TrimPrefix(path.Clean(path.Join(path.Dir(h.request.Source), u.Path)), "/"), strings.TrimPrefix(path.Clean(u.Path), "/")}
	if strings.HasPrefix(u.Path, "/") {
		candidates = []string{strings.TrimPrefix(path.Clean(u.Path), "/")}
	}
	candidates = append(candidates, strings.TrimLeft(path.Clean(u.Path), "./"), strings.ToLower(u.Path), path.Base(u.Path))
	for _, candidate := range candidates {
		if route, ok := h.refs[candidate]; ok {
			u.Path = route
			return "https://docs.docker.com" + u.String(), nil
		}
	}
	return "", fmt.Errorf("unresolved Docker ref %q from %q", destination, h.request.Source)
}
func (h *Hooks) render(w util.BufWriter, source []byte, n ast.Node, enter bool) (ast.WalkStatus, error) {
	switch v := n.(type) {
	case *ast.Heading:
		if enter {
			id := attr(n, "id")
			fmt.Fprintf(w, "<h%d class=\"%s scroll-mt-20 flex items-center gap-2\" id=\"%s\"><a class=\"text-black dark:text-white no-underline hover:underline\" href=\"#%s\">", v.Level, esc(attr(n, "class")), esc(id), esc(id))
		} else {
			w.WriteString("</a>")
			if tier := attr(n, "tier"); tier != "" {
				fmt.Fprintf(w, `<span class="not-prose bg-blue-500 dark:bg-blue-400 rounded-sm px-1 text-xs text-white">%s</span>`, esc(tier))
			}
			fmt.Fprintf(w, "</h%d>\n", v.Level)
		}
	case *ast.Link:
		if enter {
			href, err := h.resolve(string(v.Destination))
			if err != nil {
				return ast.WalkStop, err
			}
			rel := ""
			if strings.HasPrefix(href, "http") && strings.HasPrefix(string(v.Destination), "http") {
				rel = " rel=\"noopener\""
			}
			if strings.HasPrefix(string(v.Destination), "/") {
				w.WriteString("\n")
			}
			fmt.Fprintf(w, "<a class=\"link\" href=\"%s\"%s>", esc(strings.NewReplacer("(", "%28", ")", "%29").Replace(string(util.URLEscape([]byte(href), true)))), rel)
		} else {
			w.WriteString("</a>")
		}
	case *ast.AutoLink:
		if enter {
			href := string(v.URL(source))
			if bytes.HasPrefix(v.Label(source), []byte("www.")) {
				href = "https://" + string(v.Label(source))
			}
			if v.AutoLinkType == ast.AutoLinkEmail && !strings.HasPrefix(href, "mailto:") {
				href = "mailto:" + href
			}
			escaped := strings.NewReplacer("(", "%28", ")", "%29").Replace(string(util.URLEscape([]byte(href), true)))
			fmt.Fprintf(w, `<a class="link" href="%s" rel="noopener">%s</a>`, esc(escaped), esc(string(v.Label(source))))
		}
		return ast.WalkSkipChildren, nil
	case *ast.Image:
		if !enter {
			return ast.WalkContinue, nil
		}
		u, err := url.Parse(string(v.Destination))
		if err != nil {
			return ast.WalkStop, err
		}
		params := u.Query()
		src := u.String()
		if !u.IsAbs() && !strings.HasPrefix(src, "/") {
			base := h.request.Route
			if !h.request.Index {
				base = path.Dir(strings.TrimSuffix(base, "/")) + "/"
			}
			u.Path = path.Join(base, u.Path)
			u.RawQuery = ""
			src = "https://docs.docker.com" + u.String()
		}
		alt := esc(string(v.Text(source)))
		attrs := ""
		for _, key := range []string{"w", "h"} {
			if val := params.Get(key); val != "" {
				name := "width"
				if key == "h" {
					name = "height"
				}
				attrs += " " + name + "=\"" + esc(val) + "\""
			}
		}
		cls := "mx-auto"
		if params.Has("border") {
			cls += " border border-divider-light dark:border-divider-dark"
		}
		cls += " rounded-sm"
		fmt.Fprintf(w, "<figure x-data=\"{ zoom: false }\" @click=\"zoom = ! zoom\" class=\"cursor-pointer hover:opacity-90\"><img loading=\"lazy\" src=\"%s\" alt=\"%s\"%s class=\"%s\">", esc(src), alt, attrs, cls)
		if len(v.Title) > 0 {
			fmt.Fprintf(w, "<figcaption class=\"text-gray-200 dark:text-gray-500\">%s</figcaption>", esc(string(v.Title)))
		}
		fmt.Fprintf(w, "<template x-teleport=\"body\"><div x-show=\"zoom\" @click=\"zoom = false\" x-transition.opacity.duration.250ms class=\"fixed inset-0 z-20 flex items-center justify-center bg-black/100 p-6\"><button class=\"icon-svg fixed top-6 right-8 z-30 text-white\">%s</button><img loading=\"lazy\" class=\"max-h-full max-w-full rounded-sm\" src=\"%s\" alt=\"%s\"></div></template></figure>\n", h.icons["x-mark"], esc(src), alt)
		return ast.WalkSkipChildren, nil
	case *ast.FencedCodeBlock:
		if !enter {
			return ast.WalkContinue, nil
		}
		var code bytes.Buffer
		var exportCode bytes.Buffer
		for i := 0; i < v.Lines().Len(); i++ {
			segment := v.Lines().At(i)
			value := segment.Value(source)
			if len(bytes.TrimSpace(value)) == 0 && v.Info != nil {
				lineStart := bytes.LastIndexByte(source[:segment.Start], '\n') + 1
				original := source[lineStart:segment.Stop]
				openingStart := bytes.LastIndexByte(source[:v.Info.Segment.Start], '\n') + 1
				prefix := source[openingStart:v.Info.Segment.Start]
				indent := bytes.IndexAny(prefix, "`~")
				if indent >= 0 && indent < len(original) && len(bytes.TrimRight(original[indent:], "\n")) >= 4 && len(bytes.TrimSpace(original[:indent])) == 0 {
					value = original[indent:]
				}
			}
			code.Write(value)
			originalStart := bytes.LastIndexByte(source[:segment.Start], '\n') + 1
			original := source[originalStart:segment.Stop]
			if v.Info != nil {
				openingStart := bytes.LastIndexByte(source[:v.Info.Segment.Start], '\n') + 1
				prefix := source[openingStart:v.Info.Segment.Start]
				indent := bytes.IndexAny(prefix, "`~")
				if indent > 0 && len(bytes.TrimSpace(prefix[:indent])) == 0 && bytes.HasPrefix(original, prefix[:indent]) {
					original = original[indent:]
				}
			} else {
				original = value
			}
			if v.Info != nil {
				openingStart := bytes.LastIndexByte(source[:v.Info.Segment.Start], '\n') + 1
				prefix := source[openingStart:v.Info.Segment.Start]
				indent := bytes.IndexAny(prefix, "`~")
				if indent > 0 && len(bytes.TrimSpace(prefix[:indent])) > 0 {
					original = value
				}
			}
			if len(bytes.TrimSpace(value)) > 0 && !bytes.ContainsRune(original, '\t') {
				original = value
			}
			exportCode.Write(original)
		}
		lang := strings.Split(string(v.Language(source)), "{")[0]
		if lang == "" {
			lang = "text"
		}
		if lang == "mermaid" {
			h.metrics.Hooks["mermaid"]++
			fmt.Fprintf(w, "<pre class=\"mermaid not-prose my-4 flex justify-center bg-transparent\" data-pagefind-ignore>%s</pre>\n", esc(strings.TrimRight(code.String(), "\n")))
			return ast.WalkSkipChildren, nil
		}
		options := map[string]string{}
		var ranges [][2]int
		if v.Info != nil {
			info := string(v.Info.Text(source))
			if i := strings.Index(info, "{"); i >= 0 {
				attrs, ok := parser.ParseAttributes(text.NewReader([]byte(info[i:])))
				if !ok {
					attrs = nil // Pinned Goldmark ignores malformed attribute syntax.
				}
				for _, a := range attrs {
					key := string(a.Name)
					if key != "title" && key != "collapse" && key != "hl_lines" && key != "linenos" && !(lang == "goat" && key == "class") {
						return ast.WalkStop, fmt.Errorf("unproven fence attribute %s", key)
					}
					value := a.Value
					if b, ok := value.([]byte); ok {
						options[key] = string(b)
					} else if array, ok := value.([]any); ok {
						var values []string
						for _, x := range array {
							if b, ok := x.([]byte); ok {
								values = append(values, string(b))
							} else {
								values = append(values, fmt.Sprint(x))
							}
						}
						options[key] = strings.Join(values, " ")
					} else {
						options[key] = fmt.Sprint(value)
					}
				}
				for _, r := range strings.Fields(strings.ReplaceAll(options["hl_lines"], ",", " ")) {
					parts := strings.Split(r, "-")
					lo, err := strconv.Atoi(parts[0])
					if err != nil {
						return ast.WalkStop, err
					}
					hi := lo
					if len(parts) == 2 {
						hi, err = strconv.Atoi(parts[1])
						if err != nil {
							return ast.WalkStop, err
						}
					}
					ranges = append(ranges, [2]int{lo, hi})
				}
			}
		}
		if lang == "goat" {
			diagram := goat.BuildSVG(strings.NewReader(strings.TrimRight(code.String(), "\n")))
			svg := fmt.Sprintf(`<svg font-family="Menlo,Lucida Console,monospace" viewBox="0 0 %d %d">%s</svg>`, diagram.Width, diagram.Height, diagram.Body)
			fmt.Fprintf(w, `<div class="goat svg-container %s" data-export-code="%s">%s</div>`, esc(options["class"]), base64.StdEncoding.EncodeToString([]byte(code.String())), svg)
			return ast.WalkSkipChildren, nil
		}
		lexer := lexers.Get(lang)
		unhighlighted := lexer == nil
		codeText := strings.TrimRight(code.String(), "\n")
		var value string
		if unhighlighted {
			value = `<pre tabindex="0"><code class="language-` + esc(lang) + `" data-lang="` + esc(lang) + `">` + esc(codeText) + `</code></pre>`
		} else {
			begin := time.Now()
			tokens, err := chroma.Coalesce(lexer).Tokenise(nil, codeText)
			if err != nil {
				return ast.WalkStop, err
			}
			var highlighted bytes.Buffer
			formatter := ch.New(ch.WithClasses(true), ch.WithLineNumbers(options["linenos"] == "true"), ch.LineNumbersInTable(true), ch.HighlightLines(ranges))
			err = formatter.Format(&highlighted, styles.Fallback, tokens)
			h.metrics.ChromaNS += time.Since(begin).Nanoseconds()
			if err != nil {
				return ast.WalkStop, err
			}
			value = highlighted.String()
		}
		value = strings.ReplaceAll(value, "<pre class=\"chroma\">", "<pre tabindex=\"0\" class=\"chroma\">")
		if options["linenos"] == "true" {
			value = strings.Replace(value, `<pre tabindex="0" class="chroma"><span`, `<pre tabindex="0" class="chroma"><code><span`, 1)
			value = strings.Replace(value, `</pre></td>`, `</code></pre></td>`, 1)
		}
		value = strings.Replace(value, "<code><span class=\"line\">", "<code class=\"language-"+esc(lang)+"\" data-lang=\""+esc(lang)+"\"><span class=\"line\">", 1)
		var ordinary bytes.Buffer
		fmt.Fprintf(&ordinary, "<div data-pagefind-ignore x-data x-ref=\"root\" class=\"group mt-2 mb-4 flex w-full scroll-mt-2 flex-col items-start gap-4 rounded bg-gray-50 p-2 outline outline-1 outline-offset-[-1px] outline-gray-200 dark:bg-gray-900 dark:outline-gray-800\"><div class=\"relative w-full\"><div class=\"syntax-light dark:syntax-dark not-prose w-full\"><button x-data=\"{ code: '%s', copying: false }\" class=\"top-1 absolute right-2 z-10 text-gray-300 dark:text-gray-500\" title=\"copy\" @click=\"window.navigator.clipboard.writeText(atob(code).replaceAll(/^[\\$&gt;]\\s+/gm, '')); copying = true; setTimeout(() =&gt; copying = false, 2000);\"><span :class=\"{ 'group-hover:block' : !copying }\" class=\"icon-svg hidden\">%s</span><span :class=\"{ 'group-hover:block' : copying }\" class=\"icon-svg hidden\">%s</span></button><div class=\"highlight\">%s</div></div></div></div>\n", base64.StdEncoding.EncodeToString([]byte(codeText)), h.icons["document-duplicate"], h.icons["check-circle"], value)
		output := ordinary.String()
		originalCode := strings.TrimRight(exportCode.String(), "\n")
		if originalCode != codeText {
			metadata := ` data-export-code="` + base64.StdEncoding.EncodeToString([]byte(originalCode)) + `"`
			output = strings.Replace(output, `<button x-data=`, `<button`+metadata+` x-data=`, 1)
		}
		if unhighlighted {
			output = strings.Replace(output, `<div class="highlight">`+value+`</div>`, value, 1)
		}
		if title := options["title"]; title != "" {
			header := `<div class="flex w-full items-center gap-2"><div class="flex items-center gap-2.5 rounded bg-gray-100 px-2 py-0.5 dark:bg-gray-800"><div class="font-normal text-gray-500 dark:text-gray-200">` + esc(title) + `</div></div></div>`
			output = strings.Replace(output, `<div class="relative w-full">`, header+`<div class="relative w-full">`, 1)
			output = strings.Replace(output, `class="top-1 absolute`, `class="-top-10 absolute`, 1)
		}
		if options["collapse"] != "" && options["collapse"] != "false" && options["collapse"] != "0" {
			output = strings.Replace(output, `<div class="highlight">`, `<div x-data="{ collapse: true }" class="relative overflow-clip" x-init="$watch('collapse', value =&gt; $refs.root.scrollIntoView({ behavior: 'smooth'}))"><div x-show="collapse" class="absolute z-10 flex h-32 w-full flex-col-reverse items-center overflow-clip pb-4"><button @click="collapse = false" class="chip"><span>Show more</span><span class="icon-svg">`+h.icons["chevron-down"]+`</span></button></div><div :class="{ 'h-32': collapse }"><div class="highlight">`, 1)
			suffix := `<button @click="collapse = true" x-show="!collapse" class="chip mx-auto mt-4 flex items-center  text-sm"><span>Hide</span><span class="icon-svg">` + h.icons["chevron-up"] + `</span></button></div></div>`
			output = strings.TrimSuffix(output, "</div></div></div>\n") + suffix + "</div></div></div>\n"
		}
		w.WriteString(output)
		// The hook above emits the ordinary wrapper; add only corpus-used title/collapse behavior.
		return ast.WalkSkipChildren, nil
	case *ast.Blockquote:
		if enter {
			kind := h.alerts[n]
			cls := "admonition not-prose"
			if kind != "" {
				mapping := map[string]string{"note": "note", "important": "note", "tip": "tip", "warning": "warning", "caution": "danger"}
				cls = "admonition admonition-" + mapping[kind] + " admonition not-prose"
			}
			id := ""
			if val := attr(n, "id"); val != "" {
				id = " id=\"" + esc(val) + "\""
			}
			export := ""
			if marker := attr(n, "data-export-alert-marker"); marker != "" {
				export = " data-export-alert-marker=\"" + marker + "\""
			}
			fmt.Fprintf(w, "<blockquote%s class=\"%s\"%s>", id, cls, export)
			if kind != "" {
				icon := map[string]string{"note": "info", "important": "important", "tip": "lightbulb", "warning": "warning", "caution": "warning"}[kind]
				fmt.Fprintf(w, "<div class=\"admonition-header\"><span class=\"admonition-icon\">%s</span><span class=\"admonition-title\">%s</span></div><div class=\"admonition-content\">", h.icons["alert-"+icon], strings.ToUpper(kind[:1])+kind[1:])
			}
		} else {
			if h.alerts[n] != "" {
				w.WriteString("</div>")
			}
			w.WriteString("</blockquote>\n")
		}
	case *ea.Table:
		if enter {
			w.WriteString("<div class=\"overflow-x-auto\"><table>\n")
		} else {
			w.WriteString("</table></div>\n")
		}
	case *ea.TableHeader:
		if enter {
			w.WriteString("<thead class=\"bg-gray-100 dark:bg-gray-800\"><tr>")
		} else {
			w.WriteString("</tr></thead><tbody>")
			if n.NextSibling() == nil {
				w.WriteString("</tbody>")
			}
		}
	case *ea.TableRow:
		if enter {
			w.WriteString("<tr>")
		} else {
			w.WriteString("</tr>")
			if n.NextSibling() == nil {
				w.WriteString("</tbody>")
			}
		}
	case *ea.TableCell:
		tag := "td"
		if n.Parent().Kind() == ea.KindTableHeader {
			tag = "th"
		}
		if enter {
			align := ""
			if v.Alignment != ea.AlignNone {
				align = " style=\"text-align: " + v.Alignment.String() + "\""
			}
			fmt.Fprintf(w, "<%s class=\"p-2\"%s>", tag, align)
		} else {
			fmt.Fprintf(w, "</%s>", tag)
		}
	}
	return ast.WalkContinue, nil
}
func (h *Hooks) markAlerts(doc ast.Node, source []byte) {
	ast.Walk(doc, func(n ast.Node, enter bool) (ast.WalkStatus, error) {
		if !enter || n.Kind() != ast.KindBlockquote {
			return ast.WalkContinue, nil
		}
		p := n.FirstChild()
		if p == nil || p.Kind() != ast.KindParagraph || p.Lines().Len() == 0 {
			return ast.WalkContinue, nil
		}
		line := p.Lines().At(0)
		marker := strings.TrimSpace(string(line.Value(source)))
		if !strings.HasPrefix(marker, "[!") || !strings.Contains(marker, "]") {
			return ast.WalkContinue, nil
		}
		end := strings.Index(marker, "]")
		kind := strings.ToLower(marker[2:end])
		switch kind {
		case "note", "tip", "warning", "caution", "important":
		default:
			return ast.WalkContinue, nil
		}
		h.alerts[n] = kind
		n.SetAttributeString("data-export-alert-marker", base64.StdEncoding.EncodeToString([]byte(marker)))
		for child := p.FirstChild(); child != nil; {
			next := child.NextSibling()
			if t, ok := child.(*ast.Text); ok && t.Segment.Start < line.Stop {
				if t.Segment.Stop <= line.Stop {
					p.RemoveChild(p, child)
				} else {
					t.Segment.Start = line.Stop
					if source[t.Segment.Start] == ':' {
						t.Segment.Start++
					}
					for t.Segment.Start < t.Segment.Stop && source[t.Segment.Start] == ' ' {
						t.Segment.Start++
					}
				}
			}
			if _, ok := child.(*ast.Text); !ok {
				last := 0
				ast.Walk(child, func(desc ast.Node, entering bool) (ast.WalkStatus, error) {
					if entering {
						if t, ok := desc.(*ast.Text); ok && t.Segment.Stop > last {
							last = t.Segment.Stop
						}
					}
					return ast.WalkContinue, nil
				})
				if last > 0 && last <= line.Stop {
					p.RemoveChild(p, child)
				}
			}
			child = next
		}
		if p.FirstChild() == nil {
			n.RemoveChild(n, p)
		}
		return ast.WalkContinue, nil
	})
}

// consumeBlockAttributes covers the four standalone attributes present in the
// pinned Markdown and the legacy warning attribute in CLI descriptions. The AST
// excludes code examples, so literal braces inside fences remain untouched.
func consumeBlockAttributes(doc ast.Node, source []byte) {
	ast.Walk(doc, func(n ast.Node, enter bool) (ast.WalkStatus, error) {
		p, ok := n.(*ast.Paragraph)
		if !enter || !ok || p.Lines().Len() == 0 {
			return ast.WalkContinue, nil
		}
		line := p.Lines().At(p.Lines().Len() - 1)
		raw := strings.TrimSpace(string(line.Value(source)))
		if raw != "{ .information }" && raw != "{ .warning }" && raw != "{ #stream }" && raw != "{ #storage-driver-order }" {
			return ast.WalkContinue, nil
		}
		attributes, valid := parser.ParseAttributes(text.NewReader([]byte(raw)))
		if !valid {
			return ast.WalkContinue, nil
		}
		for child := p.FirstChild(); child != nil; {
			next := child.NextSibling()
			if t, ok := child.(*ast.Text); ok {
				if t.Segment.Start >= line.Start {
					p.RemoveChild(p, child)
				} else if t.Segment.Stop > line.Start {
					t.Segment.Stop = line.Start
					t.SetSoftLineBreak(false)
				}
			}
			child = next
		}
		if t, ok := p.LastChild().(*ast.Text); ok {
			t.SetSoftLineBreak(false)
		}
		var target ast.Node = p
		if p.Parent().Kind() == ast.KindBlockquote {
			target = p.Parent()
		} else if p.FirstChild() == nil {
			target = p.PreviousSibling()
		}
		if target != nil {
			for _, a := range attributes {
				target.SetAttribute(a.Name, a.Value)
			}
		}
		if p.FirstChild() == nil {
			p.Parent().RemoveChild(p.Parent(), p)
			return ast.WalkSkipChildren, nil
		}
		return ast.WalkContinue, nil
	})
}
func main() {
	assets := flag.String("assets", "compatibility/assets", "Docker SVG assets")
	refsFile := flag.String("refs", "", "explicit pinned source-route map")
	inspect := flag.Bool("inspect-fences", false, "validation-only Markdown fence inspection")
	flag.Parse()
	refs := map[string]string{}
	if *refsFile != "" {
		data, err := os.ReadFile(*refsFile)
		if err != nil {
			panic(err)
		}
		if err = json.Unmarshal(data, &refs); err != nil {
			panic(err)
		}
	}
	icons := map[string]string{}
	files, _ := filepath.Glob(filepath.Join(*assets, "*.svg"))
	for _, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			panic(err)
		}
		icons[strings.TrimSuffix(filepath.Base(file), ".svg")] = string(data)
	}
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 64*1024), 32*1024*1024)
	encoder := json.NewEncoder(os.Stdout)
	for scanner.Scan() {
		var request Request
		response := Response{}
		if err := json.Unmarshal(scanner.Bytes(), &request); err != nil {
			response.Error = err.Error()
			encoder.Encode(response)
			continue
		}
		hooks := &Hooks{request: request, refs: refs, icons: icons, metrics: Metrics{Hooks: map[string]int{}}, alerts: map[ast.Node]string{}}
		md := goldmark.New(goldmark.WithExtensions(extension.GFM, extension.Footnote, extension.DefinitionList), goldmark.WithParserOptions(parser.WithAttribute()), goldmark.WithRendererOptions(gh.WithUnsafe(), renderer.WithNodeRenderers(util.Prioritized(hooks, 100))))
		source := []byte(request.Markdown)
		start := time.Now()
		doc := md.Parser().Parse(text.NewReader(source), parser.WithContext(parser.NewContext(parser.WithIDs(&dockerIDs{used: map[string]bool{}, metrics: &hooks.metrics}))))
		hooks.metrics.MarkdownParseNS = time.Since(start).Nanoseconds() - hooks.metrics.HookNS
		if *inspect {
			response.Fences = []string{}
			ast.Walk(doc, func(n ast.Node, enter bool) (ast.WalkStatus, error) {
				if enter && n.Kind() == ast.KindFencedCodeBlock {
					var b bytes.Buffer
					for i := 0; i < n.Lines().Len(); i++ {
						segment := n.Lines().At(i)
						b.Write(segment.Value(source))
					}
					response.Fences = append(response.Fences, strings.TrimRight(b.String(), "\n"))
				}
				return ast.WalkContinue, nil
			})
			encoder.Encode(response)
			continue
		}
		start = time.Now()
		previousHookNS := hooks.metrics.HookNS
		ids := &dockerIDs{used: map[string]bool{}, metrics: &hooks.metrics}
		ast.Walk(doc, func(n ast.Node, enter bool) (ast.WalkStatus, error) {
			if enter && n.Kind() == ast.KindHeading {
				if id := attr(n, "id"); id != "" {
					ids.Put([]byte(id))
				} else {
					var headingText strings.Builder
					ast.Walk(n, func(child ast.Node, entry bool) (ast.WalkStatus, error) {
						if !entry {
							return ast.WalkContinue, nil
						}
						switch t := child.(type) {
						case *ast.RawHTML:
							return ast.WalkSkipChildren, nil
						case *ast.Text:
							headingText.Write(util.UnescapePunctuations(t.Value(source)))
						case *ast.String:
							headingText.Write(t.Value)
						}
						return ast.WalkContinue, nil
					})
					plain := stdhtml.UnescapeString(headingText.String())
					id := ids.Generate([]byte(plain), ast.KindHeading)
					if legacy, ok := request.LegacyAnchors[string(id)]; ok && strings.Contains(string(n.Text(source)), "data-docker-slot") {
						id = []byte(legacy)
						ids.Put(id)
					}
					n.SetAttributeString("id", id)
				}
			}
			return ast.WalkContinue, nil
		})
		consumeBlockAttributes(doc, source)
		hooks.markAlerts(doc, source)
		hooks.metrics.HookNS += time.Since(start).Nanoseconds() - (hooks.metrics.HookNS - previousHookNS)
		var output bytes.Buffer
		start = time.Now()
		before := hooks.metrics.HookNS
		err := md.Renderer().Render(&output, source, doc)
		hooks.metrics.MarkdownRenderNS = time.Since(start).Nanoseconds() - (hooks.metrics.HookNS - before) - hooks.metrics.ChromaNS
		if err != nil {
			response.Error = err.Error()
		} else {
			response.HTML = output.String()
		}
		response.Metrics = hooks.metrics
		encoder.Encode(response)
	}
	if err := scanner.Err(); err != nil {
		panic(err)
	}
}
