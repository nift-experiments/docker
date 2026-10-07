// Copyright 2019 The Hugo Authors. All rights reserved.
// Licensed under the Apache License, Version 2.0.
// Adapted only the GitHub anchor algorithm required by pinned Docker Docs:
// https://github.com/gohugoio/hugo/blob/4a9485336a3f/markup/goldmark/autoid.go
// No Blackfriday, alternate dialects or generic Hugo ID configuration.
package main

import (
	"fmt"
	"github.com/yuin/goldmark/ast"
	"strings"
	"time"
	"unicode"
)

type dockerIDs struct {
	used    map[string]bool
	metrics *Metrics
}

func (ids *dockerIDs) Generate(value []byte, kind ast.NodeKind) []byte {
	begin := time.Now()
	defer func() { ids.metrics.HookNS += time.Since(begin).Nanoseconds() }()
	var out strings.Builder
	for _, r := range strings.TrimSpace(string(value)) {
		switch {
		case r == '-' || r == ' ':
			out.WriteByte('-')
		case r == '_' || unicode.IsLetter(r) || unicode.IsDigit(r):
			out.WriteRune(unicode.ToLower(r))
		}
	}
	base := out.String()
	if base == "" {
		base = "id"
		if kind == ast.KindHeading {
			base = "heading"
		}
	}
	result := base
	for suffix := 1; ids.used[result]; suffix++ {
		result = fmt.Sprintf("%s-%d", base, suffix)
	}
	ids.used[result] = true
	return []byte(result)
}
func (ids *dockerIDs) Put(value []byte) { ids.used[string(value)] = true }
