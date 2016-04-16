# FlowIDE

Add first-class Flow support to Sublime Text! FlowIDE provides autocomplete, diagnostics, type hints, and jump-to-definition for the [Flow](http://flowtype.org/) static type checker for JS. FlowIDE provides the majority of Flow-related features implemented in Facebook's [Nuclide](http://nuclide.io/).

## Requirements
You'll need Sublime Text build `3070` or greater (tooltip support). Neither FlowIDE nor Flow support Windows.

## Usage
Install with Package Control!

FlowIDE features only activate on files with the `// @flow` or `/* @flow */` declarations. It automatically determines the root directory and `.flowconfig` of the file you're currently working on.

FlowIDE works out-of-the-box if the `flow` binary is in your `PATH`. To fit your needs, you can change the following settings: 
- `flow_path` (string): the path to your `flow` binary.
- `use_npm_flow` (boolean): if true, uses the binary from the npm `flow-bin` package in the `node_modules` of your current file's root directory. Using `flow-bin`'s binary will slow down editing features because it is wrapped in a Node script and starts an interpreter on each run.

### Diagnostics and Autocomplete
Just works! Autocomplete generates snippets with parameter names when pressing `Enter`.

### Type Hints
Press `Command+Option+T` (`Control+Alt+T`) to view the type of the variable or function underneath your cursor.

### Jump-to-Definition
Press `Command+Option+J` (`Control+Alt+J`) to jump to the definition of the variable, function, or type underneath your cursor.
