// Package mindforge embeds prompt-only writing guidance and reference
// dictionaries for explicit CLI commands. Optional Python terminology
// tools are not installed by the default profile.
package mindforge

import "embed"

//go:embed hooks/inject-style-rules.sh hooks/style-rules-zh.md hooks/style-rules-en.md hooks/terminology.tsv hooks/project-dict-template.tsv
var Assets embed.FS

// RuntimeFiles lists the embedded files that an install writes into a
// platform's hook directory. Order is preserved; shell scripts must be
// executable after extraction.
var RuntimeFiles = []string{
	"hooks/inject-style-rules.sh",
	"hooks/style-rules-zh.md",
	"hooks/style-rules-en.md",
}

// BundledDictPath is the optional dictionary reference reported by doctor.
const BundledDictPath = "hooks/terminology.tsv"

const ProjectDictTemplatePath = "hooks/project-dict-template.tsv"
