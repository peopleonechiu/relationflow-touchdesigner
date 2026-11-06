# Third-party notices and provenance

This source snapshot omits model weights and runtime binaries. These notices document referenced dependencies and the terms that require review before distributing a complete TOX.

- **RelateAnything**, Copyright © 2026 Maëlic Neau: AGPL-3.0-only with additional section 7 terms; see [LICENSE](LICENSE), [NOTICE](NOTICE), and [upstream repository](https://github.com/Maelic/RelateAnything). Portions of the browser code adapt its inference and post-processing. The upstream current notice was retrieved at commit `fc626d0d58113efcc8b08252c168a7ad529a171f`; this does not establish the exact upstream revision used for every local file.
- **DINOv3**, Meta: the relationship and predicate models are identified upstream as DINOv3 derivatives, subject to the [DINOv3 License](DINOV3_LICENSE.md). Include that license with any distributed weights and comply with its terms. See [RelateAnything licensing](https://github.com/Maelic/RelateAnything#license) and [DINOv3](https://github.com/facebookresearch/dinov3).
- **Ultralytics YOLO / YOLOE**: model and export components have separate AGPL-3.0 obligations; see [Ultralytics licensing](https://github.com/ultralytics/ultralytics/blob/main/LICENSE) and [RelateAnything third-party notices](https://github.com/Maelic/RelateAnything/blob/main/THIRD_PARTY_NOTICES.md). Before any binary release, establish exact artifact versions, corresponding source, and export scripts.
- **ONNX Runtime Web**, Microsoft: MIT; see [ONNX Runtime](https://github.com/microsoft/onnxruntime/blob/main/LICENSE). Runtime binaries are omitted here.
- **OpenAI CLIP tokenizer**: tokenizer resources are omitted here; see [OpenAI CLIP license](https://github.com/openai/CLIP/blob/main/LICENSE). Dataset and class-label provenance should be checked before a binary/data release.

The TOX also contains assets not audited here. This notice is not a statement that distributing an existing TOX is compliant; review actual embedded content, exact upstream revisions, notices, and corresponding source before releasing one.
