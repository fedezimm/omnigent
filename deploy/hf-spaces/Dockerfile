# Hugging Face Spaces (Docker SDK) entrypoint. HF builds a Dockerfile at the
# Space repo root and runs it, routing to the `app_port` in the README
# front-matter. This shim just pulls the prebuilt image.
#
# Pinned to a release tag instead of :latest so deploys are reproducible and
# immune to tag-mutation attacks.  Update the tag when cutting a new release.
FROM ghcr.io/omnigent-ai/omnigent-server:main
