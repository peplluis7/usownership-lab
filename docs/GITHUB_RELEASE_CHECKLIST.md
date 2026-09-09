# GitHub release checklist

1. Confirm the public author list in `CITATION.cff`.
2. Choose the software licence in `LICENSE` before calling the repository open source.
3. Create a repository, e.g. `usownership-ai-transition`.
4. Push release v0.3.0.
5. Verify the CI workflow passes.
6. Run **Full paper reproduction** manually in GitHub Actions and retain its artifact.
7. Create a tagged release `v0.3.0`.
8. After journal/preprint metadata are final, update `CITATION.cff`.
9. Optionally connect the repository to Zenodo and archive the tagged release for a software DOI.
10. Add the repository/software DOI to the manuscript Data and Code Availability statement.

Suggested local commands:

```bash
git init
git add .
git commit -m "Release v0.3.0: usownership AI-transition simulation"
git branch -M main
git remote add origin <YOUR-GITHUB-REPOSITORY-URL>
git push -u origin main
git tag -a v0.3.0 -m "Paper simulation release v0.3.0"
git push origin v0.3.0
```
