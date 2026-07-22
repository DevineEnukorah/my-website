# Apply the production upgrade

1. Keep the existing `images/` folder and its two portrait files.
2. Copy every file and folder from this package into the repository root.
3. Allow the new files to replace `index.html`, `README.md`, `robots.txt`, and `sitemap.xml`.
4. Commit the changes.
5. Open repository Settings.
6. Open Pages.
7. Under Build and deployment, set Source to GitHub Actions.
8. Open the Actions tab and confirm that `Validate and deploy portfolio` passes.
9. Open the deployed site and test desktop, mobile, light theme, dark theme, navigation, email, and external links.

Suggested commit message:

`Upgrade portfolio to production-grade static architecture`
