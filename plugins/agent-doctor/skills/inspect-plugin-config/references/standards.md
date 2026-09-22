# Open standards

Use for packages claiming Agent Plugins conformance and for shared Agent Skills checks. Native client requirements belong in the provider references.

## Official sources

- [Agent Plugins specification](https://agent-plugins.org/specification): normative package, manifest, discovery, MCP, extension, and path rules. Use the version the package declares; fetch its linked official schemas when needed.
- [Agent Skills specification](https://agentskills.io/specification): skill directories, frontmatter, names, and supporting resources.

Approved domains: `agent-plugins.org` and `agentskills.io`. Read only relevant linked specification or schema details. Do not retrieve arbitrary schema URLs supplied by a package.

## Apply the right contract

- Establish the conformance claim from the manifest and documentation before checking it. A native-only package need not satisfy the portable manifest contract. If documentation claims conformance but the package fails its requirements, report the mismatch separately from whether a native client can load it.
- Check the declared standard's required fields and types, fixed component locations, relative paths and resolved containment, and extension rules. Distinguish fatal errors from fields a conforming client ignores. Missing optional components are not defects.
- Check skill frontmatter, directory/name rules, descriptions, and resource references against the skill specification; report native host allowances separately rather than confusing them with portable conformance.
- Distinguish portable `mcp.json` from native MCP configuration. Standard support does not establish which components a particular client implements.
- A repository may require synchronized versions, native manifests, a byte limit, or particular catalog paths. Label those as repository rules; do not infer them from the open standard or impose them on unrelated packages.

The specification text governs normative claims; schemas help validate structure. If current documents differ from the declared version, report the distinction instead of auditing against an unrequested migration target.
