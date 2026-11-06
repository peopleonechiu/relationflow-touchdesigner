# TouchDesigner relationship detection prototype

**Based on [RelateAnything by Maëlic Neau](https://github.com/Maelic/RelateAnything). Built with DINOv3.**

An experimental TouchDesigner integration for object detection and open-vocabulary relationship scoring. The prototype combines a local browser runtime, YOLO object detection, and the upstream relationship model. The parameter interface supports relationship phrases, object classes, confidence thresholds and an overlay; output is designed for CHOP and DAT workflows.

## Availability and limitations

This is an initial **source snapshot**, not a downloadable or reproducible TOX release. The TOX, model weights, ONNX Runtime binaries, tokenizer data, and sample media are not included. The repository does not yet include an automated builder or all corresponding build/export materials. Do not expect cloning this repository to produce a working plugin.

The local prototype was tested on one Apple Silicon Mac with TouchDesigner 2025.33230. Windows and other Macs have not been verified. Both an 8 GB MacBook Air and an 8 GB Windows computer have been reported to remain at loading; the cause is not yet known. These reports do not establish whether RAM capacity is the cause. The files in this repository can differ from the locally exported prototype.

## Code and attribution

Parts of `browser/js` adapt the browser inference and post-processing work from [RelateAnything](https://github.com/Maelic/RelateAnything), Copyright © 2026 Maëlic Neau. The code in this snapshot is offered under AGPL-3.0-only; see [LICENSE](LICENSE) and the upstream [NOTICE](NOTICE), including its additional attribution and name-use terms. This project is independent and is not endorsed by the upstream author. The upstream license also requires attribution in appropriate legal notices for interactive interfaces; this must be verified for every distributed build.

This source snapshot refers to third-party assets with separate terms. The relation and predicate models are derivatives of Meta DINOv3; see [DINOV3_LICENSE.md](DINOV3_LICENSE.md). Ultralytics-derived detector models are subject to AGPL-3.0. ONNX Runtime Web is MIT-licensed. More details and source links are in [THIRD_PARTY.md](THIRD_PARTY.md). Different terms can apply to weights, datasets, and custom user models. No model license is replaced by this repository's code license.

## Files

- `browser/`: browser-side runtime source and detector metadata; runtime/model assets are omitted.
- `td/`: TouchDesigner callback and integration scripts; an automated component builder is not yet provided.
- `tests/`: protocol, validation, and browser startup tests. Some tests require dependencies or assets that are not included.
- `CUSTOM_MODEL_AGENT_PROMPT.md`: experimental custom detector format guidance.

For research attribution, please cite [RelateAnything](https://github.com/Maelic/RelateAnything#citation) and [DINOv3](https://github.com/facebookresearch/dinov3#citing-dinov3) as applicable.
