// Standalone publication minifier; no Hugo or Markdown dependency.
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"github.com/tdewolff/minify/v2"
	"github.com/tdewolff/minify/v2/css"
	"github.com/tdewolff/minify/v2/html"
	"github.com/tdewolff/minify/v2/js"
	mj "github.com/tdewolff/minify/v2/json"
	"github.com/tdewolff/minify/v2/svg"
	"os"
)

type Request struct{ Path string }

func main() {
	m := minify.New()
	m.Add("text/html", &html.Minifier{KeepDocumentTags: true, KeepEndTags: true, KeepSpecialComments: true, KeepDefaultAttrVals: true})
	m.AddFunc("text/css", css.Minify)
	m.Add("application/javascript", &js.Minifier{Version: 2022})
	m.AddFunc("application/json", mj.Minify)
	m.Add("image/svg+xml", &svg.Minifier{KeepNamespaces: []string{"", "x-bind"}})
	scan := bufio.NewScanner(os.Stdin)
	encoder := json.NewEncoder(os.Stdout)
	for scan.Scan() {
		var request Request
		var err error
		if err = json.Unmarshal(scan.Bytes(), &request); err != nil {
			panic(err)
		}
		input, err := os.ReadFile(request.Path)
		if err != nil {
			panic(err)
		}
		result, err := m.Bytes("text/html", input)
		if err != nil {
			panic(fmt.Errorf("%s: %w", request.Path, err))
		}
		if string(input) != string(result) {
			if err = os.WriteFile(request.Path, result, 0644); err != nil {
				panic(err)
			}
		}
		encoder.Encode(map[string]any{"path": request.Path, "input_bytes": len(input), "output_bytes": len(result)})
	}
	if err := scan.Err(); err != nil {
		panic(err)
	}
}
