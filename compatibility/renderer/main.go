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
	"strings"
	"time"

	"github.com/alecthomas/chroma/v2"
	ch "github.com/alecthomas/chroma/v2/formatters/html"
	"github.com/alecthomas/chroma/v2/lexers"
	"github.com/alecthomas/chroma/v2/styles"
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
}
type Metrics struct {
	MarkdownParseNS, MarkdownRenderNS, HookNS, ChromaNS int64
	Hooks                                               map[string]int
}
type Response struct {
	HTML    string
	Metrics Metrics
	Error   string
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
	for kind, name := range map[ast.NodeKind]string{ast.KindHeading: "heading", ast.KindLink: "link", ast.KindImage: "image", ast.KindFencedCodeBlock: "codeblock", ast.KindBlockquote: "blockquote", ea.KindTable: "table", ea.KindTableHeader: "table", ea.KindTableRow: "table", ea.KindTableCell: "table"} {
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
	candidates := []string{strings.TrimPrefix(path.Clean(path.Join(path.Dir(h.request.Source), u.Path)), "/"), strings.TrimPrefix(u.Path, "/")}
	if strings.HasPrefix(u.Path, "/") {
		candidates = []string{strings.TrimPrefix(u.Path, "/")}
	}
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
			fmt.Fprintf(w, "</a></h%d>\n", v.Level)
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
			fmt.Fprintf(w, "<a class=\"link\" href=\"%s\"%s>", esc(href), rel)
		} else {
			w.WriteString("</a>")
		}
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
		for i := 0; i < v.Lines().Len(); i++ {
			segment := v.Lines().At(i)
			code.Write(segment.Value(source))
		}
		lang := string(v.Language(source))
		if lang == "" {
			lang = "text"
		}
		if lang == "mermaid" {
			h.metrics.Hooks["mermaid"]++
			fmt.Fprintf(w, "<pre class=\"mermaid not-prose my-4 flex justify-center bg-transparent\" data-pagefind-ignore>%s</pre>\n", esc(strings.TrimSuffix(code.String(), "\n")))
			return ast.WalkSkipChildren, nil
		}
		if v.Info != nil && strings.Contains(string(v.Info.Text(source)), "{") {
			return ast.WalkStop, fmt.Errorf("code-fence attributes require a corpus fixture: %s", v.Info.Text(source))
		}
		begin := time.Now()
		lexer := lexers.Get(lang)
		if lexer == nil {
			lexer = lexers.Fallback
		}
		lexer = chroma.Coalesce(lexer)
		codeText := strings.TrimSuffix(code.String(), "\n")
		tokens, err := lexer.Tokenise(nil, codeText)
		if err != nil {
			return ast.WalkStop, err
		}
		var highlighted bytes.Buffer
		formatter := ch.New(ch.WithClasses(true))
		err = formatter.Format(&highlighted, styles.Fallback, tokens)
		h.metrics.ChromaNS += time.Since(begin).Nanoseconds()
		if err != nil {
			return ast.WalkStop, err
		}
		value := highlighted.String()
		value = strings.Replace(value, "<pre class=\"chroma\">", "<pre tabindex=\"0\" class=\"chroma\">", 1)
		value = strings.Replace(value, "<code>", "<code class=\"language-"+esc(lang)+"\" data-lang=\""+esc(lang)+"\">", 1)
		fmt.Fprintf(w, "<div data-pagefind-ignore x-data x-ref=\"root\" class=\"group mt-2 mb-4 flex w-full scroll-mt-2 flex-col items-start gap-4 rounded bg-gray-50 p-2 outline outline-1 outline-offset-[-1px] outline-gray-200 dark:bg-gray-900 dark:outline-gray-800\"><div class=\"relative w-full\"><div class=\"syntax-light dark:syntax-dark not-prose w-full\"><button x-data=\"{ code: '%s', copying: false }\" class=\"top-1 absolute right-2 z-10 text-gray-300 dark:text-gray-500\" title=\"copy\" @click=\"window.navigator.clipboard.writeText(atob(code).replaceAll(/^[\\$&gt;]\\s+/gm, '')); copying = true; setTimeout(() =&gt; copying = false, 2000);\"><span :class=\"{ 'group-hover:block' : !copying }\" class=\"icon-svg hidden\">%s</span><span :class=\"{ 'group-hover:block' : copying }\" class=\"icon-svg hidden\">%s</span></button><div class=\"highlight\">%s</div></div></div></div>\n", base64.StdEncoding.EncodeToString([]byte(codeText)), h.icons["document-duplicate"], h.icons["check-circle"], value)
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
			fmt.Fprintf(w, "<blockquote%s class=\"%s\">", id, cls)
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
		if !strings.HasPrefix(marker, "[!") || !strings.HasSuffix(marker, "]") {
			return ast.WalkContinue, nil
		}
		kind := strings.ToLower(marker[2 : len(marker)-1])
		switch kind {
		case "note", "tip", "warning", "caution", "important":
		default:
			return ast.WalkContinue, nil
		}
		h.alerts[n] = kind
		for child := p.FirstChild(); child != nil; {
			next := child.NextSibling()
			if t, ok := child.(*ast.Text); ok && t.Segment.Stop <= line.Stop {
				p.RemoveChild(p, child)
			}
			child = next
		}
		if p.FirstChild() == nil {
			n.RemoveChild(n, p)
		}
		return ast.WalkContinue, nil
	})
}
func main() {
	assets := flag.String("assets", "compatibility/assets", "Docker SVG assets")
	refsFile := flag.String("refs", "", "explicit pinned source-route map")
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
		md := goldmark.New(goldmark.WithExtensions(extension.GFM, extension.Footnote), goldmark.WithParserOptions(parser.WithAutoHeadingID(), parser.WithAttribute()), goldmark.WithRendererOptions(gh.WithUnsafe(), renderer.WithNodeRenderers(util.Prioritized(hooks, 100))))
		source := []byte(request.Markdown)
		start := time.Now()
		doc := md.Parser().Parse(text.NewReader(source), parser.WithContext(parser.NewContext(parser.WithIDs(&dockerIDs{used: map[string]bool{}, metrics: &hooks.metrics}))))
		hooks.metrics.MarkdownParseNS = time.Since(start).Nanoseconds() - hooks.metrics.HookNS
		start = time.Now()
		hooks.markAlerts(doc, source)
		hooks.metrics.HookNS += time.Since(start).Nanoseconds()
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
