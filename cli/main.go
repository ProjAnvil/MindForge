// Command mindforge is the MindForge installer and toolbox.
//
// MindForge ships controlled-writing rules and a translationese defense
// (zh-guard) as hook scripts. This CLI installs them into local coding
// agents, generates project dictionaries, and diagnoses the setup:
//
//	mindforge install              interactive user-level install
//	mindforge init dict            generate a project dictionary
//	mindforge doctor               check the local setup
//
// The hook executables themselves stay Python (fail-open scripts shared
// with the plugin distribution); this CLI is the installer, generator and
// doctor, not the runtime. See the repo README for the roadmap.
package main

import (
	"fmt"
	"os"
)

// Version is the CLI version. Bump per release; the release process also
// builds platform binaries with this string.
const Version = "0.1.0"

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "install":
		if err := runInstall(os.Args[2:], os.Stdin); err != nil {
			fmt.Fprintln(os.Stderr, "install:", err)
			os.Exit(1)
		}
	case "init":
		if err := runInit(os.Args[2:]); err != nil {
			fmt.Fprintln(os.Stderr, "init:", err)
			os.Exit(1)
		}
	case "doctor":
		if err := runDoctor(os.Args[2:]); err != nil {
			fmt.Fprintln(os.Stderr, "doctor:", err)
			os.Exit(1)
		}
	case "version", "--version", "-v":
		fmt.Println("mindforge " + Version)
	case "help", "--help", "-h":
		usage()
	default:
		fmt.Fprintf(os.Stderr, "unknown command: %s\n\n", os.Args[1])
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Print(`mindforge - MindForge installer and toolbox

Usage:
  mindforge install   Install writing rules and the zh-guard hooks (user level).
                      Options: --lang=zh-cn|en  --platform=claude,zcode  --yes
  mindforge init dict Generate a project-level dictionary (mindforge.zh-dict.tsv).
                      Options: --lang=zh-cn  --force
  mindforge doctor    Diagnose runtimes, hook registration and dictionary tiers.
  mindforge version   Print the CLI version.
`)
}
