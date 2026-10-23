// Package mindforge embeds the zh-guard runtime payload that the CLI
// installs: hook scripts, the bundled dictionary, and the style-rule
// documents. Keeping them embedded means a single binary carries
// everything; no separate checkout is needed at install time.
//
// Only runtime files are embedded. Test and evaluation scripts stay out.
package mindforge

import "embed"

//go:embed hooks/inject-style-rules.sh hooks/inject.py hooks/inspect.py hooks/inspect-file.py hooks/zh_guard_common.py hooks/term-dict-server.py hooks/style-rules-zh.md hooks/style-rules-en.md hooks/terminology.tsv
var Assets embed.FS

// RuntimeFiles lists the embedded files that an install writes into a
// platform's hook directory. Order is preserved; shell scripts must be
// executable after extraction.
var RuntimeFiles = []string{
	"hooks/inject-style-rules.sh",
	"hooks/inject.py",
	"hooks/inspect.py",
	"hooks/inspect-file.py",
	"hooks/zh_guard_common.py",
	"hooks/term-dict-server.py",
	"hooks/style-rules-zh.md",
	"hooks/style-rules-en.md",
	"hooks/terminology.tsv",
}

// BundledDictPath is the embedded bundled dictionary used to seed the
// user-level dictionary on first install.
const BundledDictPath = "hooks/terminology.tsv"
