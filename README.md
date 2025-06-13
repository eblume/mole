# Mole
Copyright 2025 Erich Blume <blume.erich@gmail.com>
Provided under the MIT License. See LICENSE for more information.

# About
Mole is a combination of a few ideas I'm working through within the space of
automation and workflow assistance.

I use it every day and never get enough time to develop it "properly", so it's
in a constant state of rewrite. This works for me because I if there is a
problem in code I care about, I tend to find out about it very quickly. On the
other hand, code that I haven't "quite gotten working yet" can grow stale.

It's all to say, this project isn't really ready for anyone other than myself,
and it's been that way for a few years now. If you find this, let me know what
brought you here in a github issue, maybe you'll spark an idea.

In the current iteration of this project, I am using uv to build everything. It
should behave like a typical uv / python package.

# Release
To release a new version, run `uv version --bump [patch|minor|major]` and then
`mise run release`. The release script will perform some basic sanity checks:

* Unit tests must pass (`uv run pytest`)
* The git stage must be clean
* The current version (`uv version`) must not already be tagged

Once the release-tagging script finishes, you can `git push --all` to trigger
the release build via github action.
