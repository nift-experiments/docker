// Standalone pinned publication minification; no Hugo or Markdown dependency.
package main

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"runtime"
	"runtime/pprof"
	"sync"

	"github.com/tdewolff/minify/v2"
	"github.com/tdewolff/minify/v2/css"
	"github.com/tdewolff/minify/v2/html"
	"github.com/tdewolff/minify/v2/js"
	mj "github.com/tdewolff/minify/v2/json"
	"github.com/tdewolff/minify/v2/svg"
)

type Request struct {
	Path    string
	Paths   []string
	Workers int
}
type Result struct {
	Path   string `json:"path"`
	Digest string `json:"digest"`
	Error  string `json:"error,omitempty"`
}

// This cache lasts for one invocation only. It memoizes exact SVG input and
// parameters; full publications still minify every HTML document. Its retained
// key/output bytes are bounded, including long diagram inputs.
type SVGCache struct {
	mu                  sync.Mutex
	values              map[string][]byte
	bytes, hits, misses int
}

func (cache *SVGCache) Minify(m *minify.M, w io.Writer, r io.Reader, params map[string]string) error {
	input, err := io.ReadAll(r)
	if err != nil {
		return err
	}
	options, err := json.Marshal(params)
	if err != nil {
		return err
	}
	key := string(options) + "\x00" + string(input)
	cache.mu.Lock()
	output, found := cache.values[key]
	if found {
		cache.hits++
	}
	cache.mu.Unlock()
	if !found {
		cache.mu.Lock()
		cache.misses++
		cache.mu.Unlock()
		var buffer bytes.Buffer
		base := svg.Minifier{KeepNamespaces: []string{"", "x-bind"}}
		if err = base.Minify(m, &buffer, bytes.NewReader(input), params); err != nil {
			return err
		}
		output = buffer.Bytes()
		cache.mu.Lock()
		if _, exists := cache.values[key]; !exists && cache.bytes+len(key)+len(output) <= 32*1024*1024 {
			cache.values[key] = output
			cache.bytes += len(key) + len(output)
		}
		cache.mu.Unlock()
	}
	_, err = w.Write(output)
	return err
}
func minifier(cache *SVGCache) *minify.M {
	m := minify.New()
	m.Add("text/html", &html.Minifier{KeepDocumentTags: true, KeepEndTags: true, KeepSpecialComments: true, KeepDefaultAttrVals: true})
	m.AddFunc("text/css", css.Minify)
	m.Add("application/javascript", &js.Minifier{Version: 2022})
	m.AddFunc("application/json", mj.Minify)
	m.Add("image/svg+xml", cache)
	return m
}
func process(m *minify.M, path string) Result {
	result := Result{Path: path}
	input, err := os.ReadFile(path)
	if err != nil {
		result.Error = err.Error()
		return result
	}
	output, err := m.Bytes("text/html", input)
	if err != nil {
		result.Error = err.Error()
		return result
	}
	if !bytes.Equal(input, output) {
		if err = os.WriteFile(path, output, 0644); err != nil {
			result.Error = err.Error()
			return result
		}
	}
	digest := sha256.Sum256(output)
	result.Digest = hex.EncodeToString(digest[:])
	return result
}
func main() {
	if path := os.Getenv("DOCKER_MINIFIER_CPU_PROFILE"); path != "" {
		f, err := os.Create(path)
		if err != nil {
			panic(err)
		}
		if err = pprof.StartCPUProfile(f); err != nil {
			panic(err)
		}
		defer f.Close()
		defer pprof.StopCPUProfile()
	}
	scan := bufio.NewScanner(os.Stdin)
	scan.Buffer(make([]byte, 65536), 16*1024*1024)
	encoder := json.NewEncoder(os.Stdout)
	cache := &SVGCache{values: map[string][]byte{}}
	for scan.Scan() {
		var request Request
		if err := json.Unmarshal(scan.Bytes(), &request); err != nil {
			panic(err)
		}
		if request.Path != "" {
			result := process(minifier(cache), request.Path)
			if result.Error != "" {
				panic(fmt.Errorf("%s: %s", result.Path, result.Error))
			}
			encoder.Encode(result)
			continue
		}
		workers := request.Workers
		if workers < 1 {
			workers = 8
		}
		workers = min(workers, runtime.GOMAXPROCS(0), max(1, len(request.Paths)))
		results := make([]Result, len(request.Paths))
		jobs := make(chan int)
		var wait sync.WaitGroup
		for i := 0; i < workers; i++ {
			wait.Add(1)
			go func() {
				defer wait.Done()
				m := minifier(cache)
				for index := range jobs {
					results[index] = process(m, request.Paths[index])
				}
			}()
		}
		for index := range request.Paths {
			jobs <- index
		}
		close(jobs)
		wait.Wait()
		encoder.Encode(map[string]any{"results": results, "workers": workers, "svg_cache_hits": cache.hits, "svg_cache_misses": cache.misses, "svg_cache_retained_bytes": cache.bytes})
	}
	if err := scan.Err(); err != nil {
		panic(err)
	}
}
