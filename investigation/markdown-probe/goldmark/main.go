package main
import (
 "os"
 "github.com/yuin/goldmark"
 "github.com/yuin/goldmark/extension"
 "github.com/yuin/goldmark/parser"
 "github.com/yuin/goldmark/renderer/html"
)
func main(){
 source,err:=os.ReadFile(os.Args[1]);if err!=nil{panic(err)}
 md:=goldmark.New(goldmark.WithExtensions(extension.GFM,extension.Footnote),goldmark.WithParserOptions(parser.WithAutoHeadingID(),parser.WithAttribute()),goldmark.WithRendererOptions(html.WithUnsafe()))
 if err:=md.Convert(source,os.Stdout);err!=nil{panic(err)}
}
