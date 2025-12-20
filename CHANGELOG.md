# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0](https://github.com/rknightion/autopi-ha/compare/v0.7.2...v0.8.0) (2025-12-20)


### Features

* add endpoint support methods to coordinator ([d5003b6](https://github.com/rknightion/autopi-ha/commit/d5003b60911908b7b8379207e572509d6debecf2))
* add enhanced startup logging with configuration summary ([1c8c677](https://github.com/rknightion/autopi-ha/commit/1c8c677f6825b51ca59e72585e8bd9f13ddf6989))
* add unsupported endpoint logging ([42e3d78](https://github.com/rknightion/autopi-ha/commit/42e3d781d9f11eba4bad36dc63b5fc1248a97386))
* **autopi:** add fleet sensors & events ([e43858c](https://github.com/rknightion/autopi-ha/commit/e43858cb69891d67bce366f30cffe7facb906137))
* integrate endpoint support in entities ([d0f252e](https://github.com/rknightion/autopi-ha/commit/d0f252ea44e981f3537bc508f14752a832b30b91))


### Bug Fixes

* **deps:** update dependency aiohttp to v3.13.1 ([36cafd1](https://github.com/rknightion/autopi-ha/commit/36cafd1968431c70ebc8c0a433268e63c9f8b76d))
* **deps:** update dependency aiohttp to v3.13.1 ([71e65c0](https://github.com/rknightion/autopi-ha/commit/71e65c07cc660949f0f727c2bd23413393beed5f))
* handle 404 errors gracefully in coordinator ([0b44483](https://github.com/rknightion/autopi-ha/commit/0b4448327ddd2ec39ad5197a8a636a3f9fe448dd))
* improve API error handling and logging ([bf967d7](https://github.com/rknightion/autopi-ha/commit/bf967d774dfb562d04d9409c934ef386eae60a58))


### Documentation

* add comprehensive integration documentation and enhance SEO ([188d55c](https://github.com/rknightion/autopi-ha/commit/188d55c295a6eca404bc424dcd049211359ee01b))
* add new entities ([a3c6653](https://github.com/rknightion/autopi-ha/commit/a3c665392481815d9fdfd0fd4fe26ba578ff4cd6))
* update installation instructions for HACS default store ([9cf134d](https://github.com/rknightion/autopi-ha/commit/9cf134da217621dbf066def750c068da49f0b1f2))


### Miscellaneous Chores

* add config/ directory to gitignore ([985271a](https://github.com/rknightion/autopi-ha/commit/985271ad9b6defd32752a6bb0d2355553ab9872e))
* **ci:** remove AI-powered issue summarization workflow ([a62e085](https://github.com/rknightion/autopi-ha/commit/a62e085050ec9abfb318d9543fafa67db81f47e4))
* **deps:** lock file maintenance ([#101](https://github.com/rknightion/autopi-ha/issues/101)) ([8f35d2a](https://github.com/rknightion/autopi-ha/commit/8f35d2a80903567b38dcf40d4627862ef329e6b7))
* **deps:** lock file maintenance ([#109](https://github.com/rknightion/autopi-ha/issues/109)) ([f4b0999](https://github.com/rknightion/autopi-ha/commit/f4b0999989eb2aacece429ee6fc6813a4e5abe7a))
* **deps:** lock file maintenance ([#114](https://github.com/rknightion/autopi-ha/issues/114)) ([0c97946](https://github.com/rknightion/autopi-ha/commit/0c97946f194074d1412d2cdacbf403103e0d56e7))
* **deps:** lock file maintenance ([#117](https://github.com/rknightion/autopi-ha/issues/117)) ([a1b1794](https://github.com/rknightion/autopi-ha/commit/a1b179428ef627ccde7eec628836446293cb1f7f))
* **deps:** lock file maintenance ([#124](https://github.com/rknightion/autopi-ha/issues/124)) ([de7204e](https://github.com/rknightion/autopi-ha/commit/de7204e60bf051c233c211845630e053d403b944))
* **deps:** lock file maintenance ([#137](https://github.com/rknightion/autopi-ha/issues/137)) ([c5b70b6](https://github.com/rknightion/autopi-ha/commit/c5b70b6fac49f9c6177fe3af7bfd5aa8621cd769))
* **deps:** lock file maintenance ([#160](https://github.com/rknightion/autopi-ha/issues/160)) ([afb4e7f](https://github.com/rknightion/autopi-ha/commit/afb4e7f1f11a618a0c9ed3d54b0191ba63a05657))
* **deps:** lock file maintenance ([#54](https://github.com/rknightion/autopi-ha/issues/54)) ([8b0f9f9](https://github.com/rknightion/autopi-ha/commit/8b0f9f91712b8ce404b7edcb06249740bee64dbf))
* **deps:** lock file maintenance ([#66](https://github.com/rknightion/autopi-ha/issues/66)) ([3c93c02](https://github.com/rknightion/autopi-ha/commit/3c93c02e2ce072e83bca32d4f19d5508511aa0da))
* **deps:** lock file maintenance ([#69](https://github.com/rknightion/autopi-ha/issues/69)) ([2160a3a](https://github.com/rknightion/autopi-ha/commit/2160a3a834a9f609799d0d4217b10c8714d5fb68))
* **deps:** lock file maintenance ([#76](https://github.com/rknightion/autopi-ha/issues/76)) ([ce7c76e](https://github.com/rknightion/autopi-ha/commit/ce7c76eecae6d4a0dea3a21da10319a77f53c436))
* **deps:** lock file maintenance ([#84](https://github.com/rknightion/autopi-ha/issues/84)) ([333cc5c](https://github.com/rknightion/autopi-ha/commit/333cc5cf1695e03bd097c58e98d4661e797cd4af))
* **deps:** lock file maintenance ([#96](https://github.com/rknightion/autopi-ha/issues/96)) ([4018c28](https://github.com/rknightion/autopi-ha/commit/4018c2867b931bae7367ed8f8306f854b4c6439c))
* **deps:** pin anthropics/claude-code-action action to 6337623 ([974e907](https://github.com/rknightion/autopi-ha/commit/974e907b2d8ecea5861b1b41bd253b87e20791d1))
* **deps:** pin dependencies ([65c60d5](https://github.com/rknightion/autopi-ha/commit/65c60d53466377a308f08b101c1d218fe8eaeed2))
* **deps:** update actions/checkout action to v5.0.1 ([f5824c8](https://github.com/rknightion/autopi-ha/commit/f5824c8c733c1a9f145afb170a199458f55f5d63))
* **deps:** update actions/checkout action to v5.0.1 ([#126](https://github.com/rknightion/autopi-ha/issues/126)) ([665768f](https://github.com/rknightion/autopi-ha/commit/665768fa927d22b7ad115223f82939c2585a501e))
* **deps:** update actions/checkout action to v6 ([539b4c6](https://github.com/rknightion/autopi-ha/commit/539b4c6245924e741e2434a238649a6d5676942b))
* **deps:** update actions/checkout action to v6 ([663bbde](https://github.com/rknightion/autopi-ha/commit/663bbdebcf5790b6f33448cd493acb4aa723c31d))
* **deps:** update actions/checkout action to v6 ([#131](https://github.com/rknightion/autopi-ha/issues/131)) ([3592695](https://github.com/rknightion/autopi-ha/commit/35926954ddbf7e890258e877a0bda0e406267ead))
* **deps:** update actions/checkout action to v6.0.1 ([#153](https://github.com/rknightion/autopi-ha/issues/153)) ([bf7f18b](https://github.com/rknightion/autopi-ha/commit/bf7f18b397cda21efb437c79e4fa84bee0e69177))
* **deps:** update actions/checkout digest to 8e8c483 ([#152](https://github.com/rknightion/autopi-ha/issues/152)) ([4c6ec3e](https://github.com/rknightion/autopi-ha/commit/4c6ec3e7763211ebaf00d3fa771331cb3f72e694))
* **deps:** update actions/checkout digest to 93cb6ef ([#125](https://github.com/rknightion/autopi-ha/issues/125)) ([3c8dac3](https://github.com/rknightion/autopi-ha/commit/3c8dac3efdd27ee4ad4b4a3fc4dc37c3f0350d29))
* **deps:** update actions/dependency-review-action action to v4.7.3 ([#41](https://github.com/rknightion/autopi-ha/issues/41)) ([827c8dc](https://github.com/rknightion/autopi-ha/commit/827c8dcb3590355567abaa5282a43dd4bb11c678))
* **deps:** update actions/dependency-review-action action to v4.8.0 ([#73](https://github.com/rknightion/autopi-ha/issues/73)) ([452ea83](https://github.com/rknightion/autopi-ha/commit/452ea833937321b13a720d4d1a4e1ca6ee9e2e55))
* **deps:** update actions/dependency-review-action action to v4.8.1 ([#94](https://github.com/rknightion/autopi-ha/issues/94)) ([d1aeec7](https://github.com/rknightion/autopi-ha/commit/d1aeec7817e32052fd6d5e7221cb8eafc2e3899a))
* **deps:** update actions/dependency-review-action action to v4.8.2 ([#118](https://github.com/rknightion/autopi-ha/issues/118)) ([cf3574e](https://github.com/rknightion/autopi-ha/commit/cf3574e15d86aaeb8a8ff77e93395686774c0c93))
* **deps:** update actions/setup-python action to v6 ([#52](https://github.com/rknightion/autopi-ha/issues/52)) ([20f67b2](https://github.com/rknightion/autopi-ha/commit/20f67b2a65087d2b4b6c1160fd74c5f79d350b3f))
* **deps:** update actions/setup-python action to v6.1.0 ([#142](https://github.com/rknightion/autopi-ha/issues/142)) ([6ce0aa6](https://github.com/rknightion/autopi-ha/commit/6ce0aa62cf112e41b3080f4302b75bb9079f6df4))
* **deps:** update actions/stale action to v10 ([#53](https://github.com/rknightion/autopi-ha/issues/53)) ([ea58306](https://github.com/rknightion/autopi-ha/commit/ea58306fbf7b2ddc63a9e7347c58d2322a01a102))
* **deps:** update actions/stale action to v10.1.0 ([#83](https://github.com/rknightion/autopi-ha/issues/83)) ([1d47a10](https://github.com/rknightion/autopi-ha/commit/1d47a10707c69bfdc3bf6347b18fd826543e80ce))
* **deps:** update actions/stale action to v10.1.1 ([#154](https://github.com/rknightion/autopi-ha/issues/154)) ([048b8e6](https://github.com/rknightion/autopi-ha/commit/048b8e64d7de717639a238fb895620ded7fb5feb))
* **deps:** update actions/upload-artifact action to v5 ([#105](https://github.com/rknightion/autopi-ha/issues/105)) ([9e5892c](https://github.com/rknightion/autopi-ha/commit/9e5892c2afc530173b2792bfc0c8610d5bc75b75))
* **deps:** update actions/upload-artifact action to v6 ([#174](https://github.com/rknightion/autopi-ha/issues/174)) ([6635ee0](https://github.com/rknightion/autopi-ha/commit/6635ee03ba583d051fcb7797920a16e17eead8be))
* **deps:** update anthropics/claude-code-action digest to 0d19335 ([#178](https://github.com/rknightion/autopi-ha/issues/178)) ([da9ce29](https://github.com/rknightion/autopi-ha/commit/da9ce29ba8326faf2c3ab12c714cbd9af5c7f851))
* **deps:** update anthropics/claude-code-action digest to 7145c3e ([#182](https://github.com/rknightion/autopi-ha/issues/182)) ([07aa5b5](https://github.com/rknightion/autopi-ha/commit/07aa5b5bfe7f721b0847e4645d269ce86931696d))
* **deps:** update anthropics/claude-code-action digest to f0c8eb2 ([#166](https://github.com/rknightion/autopi-ha/issues/166)) ([710c1d8](https://github.com/rknightion/autopi-ha/commit/710c1d87dbb9caf2e548640a9ba2d3fa6a5af649))
* **deps:** update astral-sh/setup-uv action to v6.6.1 ([#45](https://github.com/rknightion/autopi-ha/issues/45)) ([4120898](https://github.com/rknightion/autopi-ha/commit/4120898815d5b87cd3f192b921656e8f48f4e6fb))
* **deps:** update astral-sh/setup-uv action to v6.7.0 ([#64](https://github.com/rknightion/autopi-ha/issues/64)) ([598625b](https://github.com/rknightion/autopi-ha/commit/598625baa4cb432ef8d981945cc20dc05e9609c5))
* **deps:** update astral-sh/setup-uv action to v6.8.0 ([#77](https://github.com/rknightion/autopi-ha/issues/77)) ([fc2d651](https://github.com/rknightion/autopi-ha/commit/fc2d651924faca31ad3a463274f50cd155daa8ae))
* **deps:** update astral-sh/setup-uv action to v7 ([#90](https://github.com/rknightion/autopi-ha/issues/90)) ([15a834a](https://github.com/rknightion/autopi-ha/commit/15a834a7a68e4f4cb9d8b21ef5961fdaae3f511f))
* **deps:** update astral-sh/setup-uv action to v7.1.0 ([#95](https://github.com/rknightion/autopi-ha/issues/95)) ([1428e9a](https://github.com/rknightion/autopi-ha/commit/1428e9a04a9d595e45dfcfa07935293331dcf5b2))
* **deps:** update astral-sh/setup-uv action to v7.1.1 ([#100](https://github.com/rknightion/autopi-ha/issues/100)) ([111ba32](https://github.com/rknightion/autopi-ha/commit/111ba32372a6241371a2782ceede275af07dcb22))
* **deps:** update astral-sh/setup-uv action to v7.1.2 ([#108](https://github.com/rknightion/autopi-ha/issues/108)) ([0f02a7d](https://github.com/rknightion/autopi-ha/commit/0f02a7d3bc6d66d44fc9c853173ee32e214ca27c))
* **deps:** update astral-sh/setup-uv action to v7.1.3 ([#119](https://github.com/rknightion/autopi-ha/issues/119)) ([7dbc384](https://github.com/rknightion/autopi-ha/commit/7dbc3847dfec94379e125f694bd3cf4d04e97ce4))
* **deps:** update astral-sh/setup-uv action to v7.1.4 ([#132](https://github.com/rknightion/autopi-ha/issues/132)) ([432617a](https://github.com/rknightion/autopi-ha/commit/432617a5dd56d83919c64054af6a5914b21992ce))
* **deps:** update astral-sh/setup-uv action to v7.1.5 ([#159](https://github.com/rknightion/autopi-ha/issues/159)) ([3b9dd9e](https://github.com/rknightion/autopi-ha/commit/3b9dd9e6b3ca97e6a380f4fad6b14bda60c99d58))
* **deps:** update astral-sh/setup-uv action to v7.1.6 ([#175](https://github.com/rknightion/autopi-ha/issues/175)) ([c25fb69](https://github.com/rknightion/autopi-ha/commit/c25fb69d2c187fe42185bf5c78c79357354bb81e))
* **deps:** update codecov/codecov-action action to v5.5.1 ([#48](https://github.com/rknightion/autopi-ha/issues/48)) ([13e82e1](https://github.com/rknightion/autopi-ha/commit/13e82e128b8bc9f9cef6f145192afd1500566c40))
* **deps:** update codecov/codecov-action action to v5.5.2 ([#167](https://github.com/rknightion/autopi-ha/issues/167)) ([fc236ec](https://github.com/rknightion/autopi-ha/commit/fc236ec38879075768849f4402dc0c396137a3da))
* **deps:** update dependency bandit to v1.9.1 ([#127](https://github.com/rknightion/autopi-ha/issues/127)) ([0c926ef](https://github.com/rknightion/autopi-ha/commit/0c926efb259dc801eff947a67a0fa7474ba65520))
* **deps:** update dependency bandit to v1.9.2 ([#136](https://github.com/rknightion/autopi-ha/issues/136)) ([3e2ff07](https://github.com/rknightion/autopi-ha/commit/3e2ff07f1fc1f01c676a6ef3110a684784284c42))
* **deps:** update dependency homeassistant-stubs to v2025.10.3 ([6983c5e](https://github.com/rknightion/autopi-ha/commit/6983c5e75e6292ada342af77efc437bdd0d2fdc0))
* **deps:** update dependency homeassistant-stubs to v2025.10.3 ([7e3e80d](https://github.com/rknightion/autopi-ha/commit/7e3e80debdf9cf9b123b78e973c9a8d946ce21db))
* **deps:** update dependency homeassistant-stubs to v2025.12.1 ([b64ee7d](https://github.com/rknightion/autopi-ha/commit/b64ee7d32ec3d1b259890160a8aad5ed27fff2c1))
* **deps:** update dependency homeassistant-stubs to v2025.12.3 ([79fe4d4](https://github.com/rknightion/autopi-ha/commit/79fe4d49f28d85eed02d579d7ced52b1b7cadca3))
* **deps:** update dependency homeassistant-stubs to v2025.12.3 ([7b594e0](https://github.com/rknightion/autopi-ha/commit/7b594e0c7381f46ae399323e695343fc9bf0a03b))
* **deps:** update dependency mypy to v1.18.1 ([#62](https://github.com/rknightion/autopi-ha/issues/62)) ([53ffcae](https://github.com/rknightion/autopi-ha/commit/53ffcaeeff048010bc6a2e28d8463f0f0a3ac0a7))
* **deps:** update dependency mypy to v1.18.2 ([#68](https://github.com/rknightion/autopi-ha/issues/68)) ([a98da3f](https://github.com/rknightion/autopi-ha/commit/a98da3faac25dde5e8aaca4b0a502541bb1e4cb1))
* **deps:** update dependency mypy to v1.19.0 ([#143](https://github.com/rknightion/autopi-ha/issues/143)) ([7c83406](https://github.com/rknightion/autopi-ha/commit/7c834063ee620d7214d9164c20c9c6af4754d3da))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.288 ([1abb07e](https://github.com/rknightion/autopi-ha/commit/1abb07e7177202a12e7a6f7da10ab519b7ce642a))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.288 ([38cb3b3](https://github.com/rknightion/autopi-ha/commit/38cb3b3255fcb797a8a84e5853e8b589dad1a9b2))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.299 ([d70fa02](https://github.com/rknightion/autopi-ha/commit/d70fa022804b31b67582e6c6d400ef1fd728dad9))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.300 ([9bae3ef](https://github.com/rknightion/autopi-ha/commit/9bae3efb9c9d3256d02b330825650a47be844332))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.300 ([9a6ee90](https://github.com/rknightion/autopi-ha/commit/9a6ee90da5340a2074ba006576ebfd20ba574736))
* **deps:** update dependency ruff to v0.12.11 ([#43](https://github.com/rknightion/autopi-ha/issues/43)) ([c8bc997](https://github.com/rknightion/autopi-ha/commit/c8bc997906ca760adbbf7f38f78d11449d9ff648))
* **deps:** update dependency ruff to v0.12.12 ([#49](https://github.com/rknightion/autopi-ha/issues/49)) ([f70bdf7](https://github.com/rknightion/autopi-ha/commit/f70bdf7486a958b11be8652df945c0144587200e))
* **deps:** update dependency ruff to v0.13.0 ([#60](https://github.com/rknightion/autopi-ha/issues/60)) ([1cdb41b](https://github.com/rknightion/autopi-ha/commit/1cdb41b3981e82a9860b4ee2119c7f70ba9657db))
* **deps:** update dependency ruff to v0.13.1 ([#67](https://github.com/rknightion/autopi-ha/issues/67)) ([ceb4166](https://github.com/rknightion/autopi-ha/commit/ceb4166716a7964947dd75e9627be430143803e8))
* **deps:** update dependency ruff to v0.13.2 ([#71](https://github.com/rknightion/autopi-ha/issues/71)) ([62a3a83](https://github.com/rknightion/autopi-ha/commit/62a3a83b8163d1659ea2ae4d40bf48bd593522a9))
* **deps:** update dependency ruff to v0.13.3 ([#82](https://github.com/rknightion/autopi-ha/issues/82)) ([b1a8a5a](https://github.com/rknightion/autopi-ha/commit/b1a8a5a71ac0b1c9bbef849ab37442b85927702a))
* **deps:** update dependency ruff to v0.14.0 ([#89](https://github.com/rknightion/autopi-ha/issues/89)) ([81e4cb8](https://github.com/rknightion/autopi-ha/commit/81e4cb83ec2456ab5ac3624f514d127de2035a9b))
* **deps:** update dependency ruff to v0.14.1 ([#97](https://github.com/rknightion/autopi-ha/issues/97)) ([bf38ecd](https://github.com/rknightion/autopi-ha/commit/bf38ecdabf4778fdf5642f427c9fa99c69076669))
* **deps:** update dependency ruff to v0.14.10 ([#179](https://github.com/rknightion/autopi-ha/issues/179)) ([67735c5](https://github.com/rknightion/autopi-ha/commit/67735c58c51badccd6bc03d56f8c9a4eaa717755))
* **deps:** update dependency ruff to v0.14.2 ([#102](https://github.com/rknightion/autopi-ha/issues/102)) ([0ef7634](https://github.com/rknightion/autopi-ha/commit/0ef7634e1e2f684fb25da6cb542af7f4c3f2460d))
* **deps:** update dependency ruff to v0.14.3 ([#113](https://github.com/rknightion/autopi-ha/issues/113)) ([025aec1](https://github.com/rknightion/autopi-ha/commit/025aec160e691ffa9b208b563688acc7e21ecb7f))
* **deps:** update dependency ruff to v0.14.4 ([#116](https://github.com/rknightion/autopi-ha/issues/116)) ([82d425c](https://github.com/rknightion/autopi-ha/commit/82d425c349c27372464ea514d2cd0fa44ccaf694))
* **deps:** update dependency ruff to v0.14.5 ([#120](https://github.com/rknightion/autopi-ha/issues/120)) ([d2f5426](https://github.com/rknightion/autopi-ha/commit/d2f5426054224ffb58908851286d2d212ff830e2))
* **deps:** update dependency ruff to v0.14.6 ([#133](https://github.com/rknightion/autopi-ha/issues/133)) ([70ce023](https://github.com/rknightion/autopi-ha/commit/70ce0235d68f601d6f6e5d7202434a0cb07cd001))
* **deps:** update dependency ruff to v0.14.7 ([#144](https://github.com/rknightion/autopi-ha/issues/144)) ([b059d42](https://github.com/rknightion/autopi-ha/commit/b059d4293619fa0f7ee07b140faffc2ee46d6ec2))
* **deps:** update dependency ruff to v0.14.8 ([#155](https://github.com/rknightion/autopi-ha/issues/155)) ([47d9064](https://github.com/rknightion/autopi-ha/commit/47d90645c7cde6b160563ca7f6ccc0e87fb7f1f5))
* **deps:** update dependency ruff to v0.14.9 ([#171](https://github.com/rknightion/autopi-ha/issues/171)) ([d0b9e45](https://github.com/rknightion/autopi-ha/commit/d0b9e452b2bc4e4024dc102525b5c64748abb1fc))
* **deps:** update development dependencies and tooling ([bef9b2b](https://github.com/rknightion/autopi-ha/commit/bef9b2b23565fc6fc4de853b86b00406671159a9))
* **deps:** update github/codeql-action action to v3.30.0 ([#46](https://github.com/rknightion/autopi-ha/issues/46)) ([12378f9](https://github.com/rknightion/autopi-ha/commit/12378f9c70d142d0ecdc0ecefe5b01e1e80df160))
* **deps:** update github/codeql-action action to v3.30.1 ([#50](https://github.com/rknightion/autopi-ha/issues/50)) ([618ab5c](https://github.com/rknightion/autopi-ha/commit/618ab5cfaf6743e19a5c64ed0168baea43b19f9f))
* **deps:** update github/codeql-action action to v3.30.2 ([#56](https://github.com/rknightion/autopi-ha/issues/56)) ([3635bd5](https://github.com/rknightion/autopi-ha/commit/3635bd5b2140c5718b0c130c8c6910a45fa9ae1e))
* **deps:** update github/codeql-action action to v3.30.3 ([#59](https://github.com/rknightion/autopi-ha/issues/59)) ([cf8cc7c](https://github.com/rknightion/autopi-ha/commit/cf8cc7c7726149ffd29a77b98834b1073e17d1e3))
* **deps:** update github/codeql-action action to v3.30.4 ([#72](https://github.com/rknightion/autopi-ha/issues/72)) ([f9105fd](https://github.com/rknightion/autopi-ha/commit/f9105fdf4bfff59a0df3b584e0ea5fe02914e2c3))
* **deps:** update github/codeql-action action to v3.30.5 ([#75](https://github.com/rknightion/autopi-ha/issues/75)) ([25b5bdf](https://github.com/rknightion/autopi-ha/commit/25b5bdf7508b34a99128476178c42eab3a016a2c))
* **deps:** update github/codeql-action action to v3.30.6 ([#81](https://github.com/rknightion/autopi-ha/issues/81)) ([9d22364](https://github.com/rknightion/autopi-ha/commit/9d223643960a1cd30e47cad1479bf833a251a412))
* **deps:** update github/codeql-action action to v3.30.7 ([#88](https://github.com/rknightion/autopi-ha/issues/88)) ([f9cbc20](https://github.com/rknightion/autopi-ha/commit/f9cbc20f65a7543133fbabffd30c69327cdd3588))
* **deps:** update github/codeql-action action to v4 ([#91](https://github.com/rknightion/autopi-ha/issues/91)) ([e0a69b1](https://github.com/rknightion/autopi-ha/commit/e0a69b18fadb0511990e4a993ce5a02bfafcdf7a))
* **deps:** update github/codeql-action action to v4.30.8 ([#93](https://github.com/rknightion/autopi-ha/issues/93)) ([31592ad](https://github.com/rknightion/autopi-ha/commit/31592ad17b8c8e82a06a9ad589a0ad579270a65e))
* **deps:** update github/codeql-action action to v4.30.9 ([#99](https://github.com/rknightion/autopi-ha/issues/99)) ([c405653](https://github.com/rknightion/autopi-ha/commit/c4056536334e186865621624f2a7c5f50bb2fc6f))
* **deps:** update github/codeql-action action to v4.31.0 ([#104](https://github.com/rknightion/autopi-ha/issues/104)) ([234aa33](https://github.com/rknightion/autopi-ha/commit/234aa33a2cba9de05c566b9c0d6488ae00b53e6c))
* **deps:** update github/codeql-action action to v4.31.2 ([#111](https://github.com/rknightion/autopi-ha/issues/111)) ([c52cbef](https://github.com/rknightion/autopi-ha/commit/c52cbefa7049ea93a22913d5fc010480e6672f2b))
* **deps:** update github/codeql-action action to v4.31.3 ([#122](https://github.com/rknightion/autopi-ha/issues/122)) ([9a31be3](https://github.com/rknightion/autopi-ha/commit/9a31be36e413ee7029048750ef511081308ac646))
* **deps:** update github/codeql-action action to v4.31.4 ([#129](https://github.com/rknightion/autopi-ha/issues/129)) ([8f772be](https://github.com/rknightion/autopi-ha/commit/8f772befeffbd51d3de9e2a9b5022b5873e6dd12))
* **deps:** update github/codeql-action action to v4.31.5 ([#141](https://github.com/rknightion/autopi-ha/issues/141)) ([46cb355](https://github.com/rknightion/autopi-ha/commit/46cb3557db0af02f0e765543e5283fd280f87e1c))
* **deps:** update github/codeql-action action to v4.31.6 ([#150](https://github.com/rknightion/autopi-ha/issues/150)) ([9127f94](https://github.com/rknightion/autopi-ha/commit/9127f94f05c7dad94dfecfc9447d8530ac34f55c))
* **deps:** update github/codeql-action action to v4.31.7 ([#157](https://github.com/rknightion/autopi-ha/issues/157)) ([beb5480](https://github.com/rknightion/autopi-ha/commit/beb5480eeda011792c41b9fdc9d7ef6a6b485cd2))
* **deps:** update github/codeql-action action to v4.31.8 ([#173](https://github.com/rknightion/autopi-ha/issues/173)) ([53c2de0](https://github.com/rknightion/autopi-ha/commit/53c2de0d21b5d2e0ea8e1ddf6980806fbb045ae7))
* **deps:** update github/codeql-action action to v4.31.9 ([#177](https://github.com/rknightion/autopi-ha/issues/177)) ([ef327e3](https://github.com/rknightion/autopi-ha/commit/ef327e374059600f40f98664f3eb87f425a9ce7f))
* **deps:** update github/codeql-action digest to 014f16e ([#121](https://github.com/rknightion/autopi-ha/issues/121)) ([124fd0b](https://github.com/rknightion/autopi-ha/commit/124fd0b3a6bbfdf32155b783a6c66302dc0abdc3))
* **deps:** update github/codeql-action digest to 0499de3 ([#110](https://github.com/rknightion/autopi-ha/issues/110)) ([bede54e](https://github.com/rknightion/autopi-ha/commit/bede54e2a7e3a43afed13062fae5e4a977abde02))
* **deps:** update github/codeql-action digest to 16140ae ([#98](https://github.com/rknightion/autopi-ha/issues/98)) ([7995e07](https://github.com/rknightion/autopi-ha/commit/7995e07bcf57cca260a8a19af16e8cbbbddb68d8))
* **deps:** update github/codeql-action digest to 192325c ([#58](https://github.com/rknightion/autopi-ha/issues/58)) ([528fba0](https://github.com/rknightion/autopi-ha/commit/528fba0ca1db27fdc8a5a814c3bf4ed1b6802452))
* **deps:** update github/codeql-action digest to 1b168cd ([#172](https://github.com/rknightion/autopi-ha/issues/172)) ([1ad2fb6](https://github.com/rknightion/autopi-ha/commit/1ad2fb649c26ddd1c969be488ccc004d38e9fe05))
* **deps:** update github/codeql-action digest to 2d92b76 ([#44](https://github.com/rknightion/autopi-ha/issues/44)) ([a361983](https://github.com/rknightion/autopi-ha/commit/a361983a1bf7f7dfbcf39a0c0a6d1c9aa1674c11))
* **deps:** update github/codeql-action digest to 303c0ae ([#70](https://github.com/rknightion/autopi-ha/issues/70)) ([cf406b2](https://github.com/rknightion/autopi-ha/commit/cf406b2b553987cda28458e49f5372b30604ce0a))
* **deps:** update github/codeql-action digest to 3599b3b ([#74](https://github.com/rknightion/autopi-ha/issues/74)) ([ed3da00](https://github.com/rknightion/autopi-ha/commit/ed3da00f0f4bd23ad9fcd86cbf1d644e35c7f2f8))
* **deps:** update github/codeql-action digest to 4e94bd1 ([#103](https://github.com/rknightion/autopi-ha/issues/103)) ([1a34d26](https://github.com/rknightion/autopi-ha/commit/1a34d26a41690f5847a68a1f46b1e639375495d1))
* **deps:** update github/codeql-action digest to 5d4e8d1 ([#176](https://github.com/rknightion/autopi-ha/issues/176)) ([abd6c22](https://github.com/rknightion/autopi-ha/commit/abd6c221b5bf8fc3ff31de2c9ec1e72c4237f2f1))
* **deps:** update github/codeql-action digest to 64d10c1 ([#80](https://github.com/rknightion/autopi-ha/issues/80)) ([19fbf6a](https://github.com/rknightion/autopi-ha/commit/19fbf6a0cd9abba3887987dd891e66ce48523efd))
* **deps:** update github/codeql-action digest to a8d1ac4 ([#87](https://github.com/rknightion/autopi-ha/issues/87)) ([d096507](https://github.com/rknightion/autopi-ha/commit/d096507470bc67cf715a940d0e9330040e27a1a0))
* **deps:** update github/codeql-action digest to cf1bb45 ([#156](https://github.com/rknightion/autopi-ha/issues/156)) ([a1036ca](https://github.com/rknightion/autopi-ha/commit/a1036ca4558f4a0078e32829425426ce7b28c814))
* **deps:** update github/codeql-action digest to d3678e2 ([#55](https://github.com/rknightion/autopi-ha/issues/55)) ([42dbeb4](https://github.com/rknightion/autopi-ha/commit/42dbeb494413da6e391809e19db5e3c5028f3587))
* **deps:** update github/codeql-action digest to e12f017 ([#128](https://github.com/rknightion/autopi-ha/issues/128)) ([60470da](https://github.com/rknightion/autopi-ha/commit/60470da3936fcd490326c2d213bcd4daca0a57f7))
* **deps:** update github/codeql-action digest to f1f6e5f ([#47](https://github.com/rknightion/autopi-ha/issues/47)) ([741b7de](https://github.com/rknightion/autopi-ha/commit/741b7de5c1979ec18135c8b2cf454a3f1f29bdf5))
* **deps:** update github/codeql-action digest to f443b60 ([#92](https://github.com/rknightion/autopi-ha/issues/92)) ([22f23de](https://github.com/rknightion/autopi-ha/commit/22f23de0851ce6d52c5576774713c1b05cdeb188))
* **deps:** update github/codeql-action digest to fdbfb4d ([#139](https://github.com/rknightion/autopi-ha/issues/139)) ([8ecce0c](https://github.com/rknightion/autopi-ha/commit/8ecce0c454f422cd920fab4469d317b08a081b43))
* **deps:** update github/codeql-action digest to fe4161a ([#149](https://github.com/rknightion/autopi-ha/issues/149)) ([0003dcd](https://github.com/rknightion/autopi-ha/commit/0003dcdb3ac0e02293c800ba56dba13d3d94e7c7))
* **deps:** update hacs/action digest to 06827d2 ([#140](https://github.com/rknightion/autopi-ha/issues/140)) ([a56adb9](https://github.com/rknightion/autopi-ha/commit/a56adb9ff8af8c2c818f1bc1aa8f6e5aea4ced81))
* **deps:** update hacs/action digest to 6f81caf ([#158](https://github.com/rknightion/autopi-ha/issues/158)) ([3c6a003](https://github.com/rknightion/autopi-ha/commit/3c6a0036108d626b0dee81bb8415d01df0a4ea15))
* **deps:** update hacs/action digest to 94334b7 ([#130](https://github.com/rknightion/autopi-ha/issues/130)) ([884349b](https://github.com/rknightion/autopi-ha/commit/884349b56fd284126ef165d8d83bcb76580413e4))
* **deps:** update home-assistant/actions digest to 01a62fa ([#134](https://github.com/rknightion/autopi-ha/issues/134)) ([178be76](https://github.com/rknightion/autopi-ha/commit/178be76bb8c18dd3b02ab85ced0aa78a58fa34c4))
* **deps:** update home-assistant/actions digest to 342664e ([#61](https://github.com/rknightion/autopi-ha/issues/61)) ([c14a522](https://github.com/rknightion/autopi-ha/commit/c14a52283806a2085c1a96f2fc96d35c70c1aae9))
* **deps:** update home-assistant/actions digest to 6778c32 ([#138](https://github.com/rknightion/autopi-ha/issues/138)) ([86f9232](https://github.com/rknightion/autopi-ha/commit/86f923290e6aa7f0d4c6dd4772cc867f013a81c6))
* **deps:** update home-assistant/actions digest to 87c064c ([#161](https://github.com/rknightion/autopi-ha/issues/161)) ([1cc8618](https://github.com/rknightion/autopi-ha/commit/1cc86187aa41de4185860f99a62c56e6e32dc579))
* **deps:** update home-assistant/actions digest to 8ca6e13 ([#112](https://github.com/rknightion/autopi-ha/issues/112)) ([3bf61c8](https://github.com/rknightion/autopi-ha/commit/3bf61c83fa7f027c0a1e702dcfca134c5babe27a))
* **deps:** update home-assistant/actions digest to e5c9826 ([#85](https://github.com/rknightion/autopi-ha/issues/85)) ([db188e0](https://github.com/rknightion/autopi-ha/commit/db188e002779e4d47095959db41754b910088d1c))
* **deps:** update ossf/scorecard-action action to v2.4.3 ([#78](https://github.com/rknightion/autopi-ha/issues/78)) ([0f6821c](https://github.com/rknightion/autopi-ha/commit/0f6821c4b16ad301b434f26099e63879da801afb))
* **deps:** update peter-evans/repository-dispatch action to v4 ([#79](https://github.com/rknightion/autopi-ha/issues/79)) ([c228c89](https://github.com/rknightion/autopi-ha/commit/c228c89b31702ce36e8af0b67bf957bbb060571d))
* **deps:** update peter-evans/repository-dispatch digest to 28959ce ([#123](https://github.com/rknightion/autopi-ha/issues/123)) ([157198c](https://github.com/rknightion/autopi-ha/commit/157198c06a06d44df53b98f216c72a105e88e4e3))
* **deps:** update project dependencies and configurations ([bc4b194](https://github.com/rknightion/autopi-ha/commit/bc4b194de04ff63a09d3a7480a47f3e91ad8abcd))
* **deps:** update step-security/harden-runner action to v2.13.1 ([#57](https://github.com/rknightion/autopi-ha/issues/57)) ([309bf13](https://github.com/rknightion/autopi-ha/commit/309bf13da9fe995bc58eecff515ef0dc0a10c20f))
* **deps:** update step-security/harden-runner action to v2.13.2 ([#115](https://github.com/rknightion/autopi-ha/issues/115)) ([ba035bb](https://github.com/rknightion/autopi-ha/commit/ba035bb14ab5fdbe3a6d81e84429ade96ec803c7))
* **deps:** update step-security/harden-runner action to v2.13.3 ([#151](https://github.com/rknightion/autopi-ha/issues/151)) ([e76f07d](https://github.com/rknightion/autopi-ha/commit/e76f07dcc78853c3971fbd8a1ef9bed2dc8b5f03))
* **deps:** update step-security/harden-runner action to v2.14.0 ([#170](https://github.com/rknightion/autopi-ha/issues/170)) ([37a0372](https://github.com/rknightion/autopi-ha/commit/37a03725d6e6be605544298537b3fd30a862716c))
* **deps:** update zizmorcore/zizmor-action action to v0.2.0 ([#65](https://github.com/rknightion/autopi-ha/issues/65)) ([6cec565](https://github.com/rknightion/autopi-ha/commit/6cec5656ef2f1557838a6ddf152408c48e226111))
* **deps:** update zizmorcore/zizmor-action action to v0.3.0 ([#135](https://github.com/rknightion/autopi-ha/issues/135)) ([38e8598](https://github.com/rknightion/autopi-ha/commit/38e85988f24987ab503a3a6f9a9ae286b1aa7ca9))
* replace manual workflows with release-please automation ([6c5b4d3](https://github.com/rknightion/autopi-ha/commit/6c5b4d3a4e6f634013514c6e7bdb849d5e27dae8))
* update dependencies and add AI chat functionality ([6459f70](https://github.com/rknightion/autopi-ha/commit/6459f70ca10cfc8704c1c5910381d3643085101d))
* update dependencies and pre-commit configuration ([b50f11d](https://github.com/rknightion/autopi-ha/commit/b50f11df9d46c99967bb4e504917ed19b61cba56))
* update project dependencies ([a1dee4b](https://github.com/rknightion/autopi-ha/commit/a1dee4b1cdf55bd9f787fae7fea93c5c25e93df3))


### Code Refactoring

* extract endpoint support tracking ([3a6f7b9](https://github.com/rknightion/autopi-ha/commit/3a6f7b95fdccf4efc8b825415d0566bc645ee1b6))
* reduce log verbosity by changing info to debug level ([6d840c7](https://github.com/rknightion/autopi-ha/commit/6d840c7705d61f2f01537d6ee173ce5fe73f8b0a))

## [Unreleased]


## [0.7.2] - 2025-08-26


### 🐛 Bug Fixes
- update dependency aiohttp to v3.12.15

### 🧰 Maintenance
92840d9 chore(deps): lock file maintenance
a0d0040 chore(deps): update actions/ai-inference action to v2.0.1 (#40)
66745b7 chore(deps): update actions/checkout action to v5
605c1ac chore(deps): update actions/ai-inference action to v2
c4275a1 chore(deps): update dependency mypy to v1.17.1
beed3a5 chore(deps): pin dependencies
fdfbf62 chore(deps): update codecov/codecov-action action to v5.5.0
28f77f0 chore(deps): update astral-sh/setup-uv action to v6.6.0
819c19b chore(deps): update zizmorcore/zizmor-action action to v0.1.2
1777970 chore(deps): update actions/dependency-review-action action to v4.7.2
36ebbef chore(deps): update actions/ai-inference action to v1.2.8
f317284 chore(deps): update home-assistant/actions digest to 72e1db9
f1691a9 chore(deps): update hacs/action digest to 885037d
9309664 chore(deps): update actions/checkout action to v4.3.0
a49bd8d chore(deps): update github/codeql-action action to v3.29.11
38686ec chore(deps): update dependency ruff to v0.12.10
51d3302 chore(deps): lock file maintenance
e5e65a0 chore(deps): update dependency homeassistant-stubs to v2025.8.3
40c237d chore(deps): update dependency pytest-homeassistant-custom-component to v0.13.272
7269409 refactor: improve error handling and logging practices

### 📋 Other Changes
- Merge pull request #39 from rknightion/renovate/lock-file-maintenance
- Merge pull request #36 from rknightion/renovate/actions-ai-inference-2.x
- Merge pull request #19 from rknightion/renovate/actions-checkout-5.x
- Merge pull request #9 from rknightion/renovate/mypy-1.x
- Merge pull request #38 from rknightion/renovate/lock-file-maintenance
- Merge pull request #37 from rknightion/renovate/pin-dependencies
- Merge pull request #35 from rknightion/renovate/codecov-codecov-action-5.x
- Merge pull request #31 from rknightion/renovate/astral-sh-setup-uv-6.x
- Merge pull request #30 from rknightion/renovate/zizmorcore-zizmor-action-0.x
- Merge pull request #28 from rknightion/renovate/actions-dependency-review-action-4.x
- Merge pull request #27 from rknightion/renovate/home-assistant-actions-digest
- Merge pull request #21 from rknightion/renovate/hacs-action-digest
- Merge pull request #18 from rknightion/renovate/actions-checkout-4.x
- Merge pull request #13 from rknightion/renovate/actions-ai-inference-1.x
- Merge pull request #8 from rknightion/renovate/aiohttp-3.x
- Merge pull request #7 from rknightion/renovate/github-codeql-action-3.x
- Merge pull request #6 from rknightion/renovate/ruff-0.x
- Merge pull request #10 from rknightion/renovate/pytest-homeassistant-custom-component-0.x
- Merge pull request #16 from rknightion/renovate/homeassistant-stubs-2025.x
- migrate fully to renovate
- update pr automerge
- Merge remote-tracking branch 'origin/main'
- prepare for hacs submission


## [0.7.1] - 2025-08-09


### 🐛 Bug Fixes
- units of measturement

### 📋 Other Changes
- docs


## [0.7.0] - 2025-08-03


### 🚗 Vehicle Features
- add auto-removal of deleted vehicles

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'


## [0.6.0] - 2025-08-03


### 🚗 Vehicle Features
- implement automatic vehicle discovery

### 📋 Other Changes
- add robots


## [0.5.0] - 2025-07-30


### 🚗 Vehicle Features
- enhance auto-zero debugging capabilities

### 🐛 Bug Fixes
- update dependency aiohttp to v3.12.15

### 🧰 Maintenance
7fe4413 chore: remove broken test
0f1c7ea refactor(auto-zero): simplify stale data detection mechanism
c7fb8db refactor: remove event type definitions from string files
679d588 chore: deps
dd9be17 chore(deps): update dependency pytest-homeassistant-custom-component to v0.13.264
f47d240 chore(deps): update dependency homeassistant-stubs to v2025.7.4

### 📋 Other Changes
- Revert "Merge remote-tracking branch 'origin/renovate/aiohttp-3.x'"
- Merge remote-tracking branch 'origin/renovate/aiohttp-3.x'
- Merge remote-tracking branch 'origin/renovate/pytest-homeassistant-custom-component-0.x'
- Merge remote-tracking branch 'origin/renovate/homeassistant-stubs-2025.x'


## [0.4.0] - 2025-07-29


### 🚗 Vehicle Features
- add state persistence for zeroed metrics
- add event types for vehicle events

### 🐛 Bug Fixes
- implement comprehensive error handling and logging

### 🧰 Maintenance
8f2dd93 refactor: simplify update interval configuration to use single unified interval
e351c26 refactor: split AutoPiDataFieldSensor for better auto-zero support
3a3055b chore: trigger build
fcb2218 chore: trigger build
c720bff ci: add workflow to trigger documentation sync
58d8508 chore: update project name and custom domain pattern

### 📚 Documentation
- expand entity documentation with comprehensive sensor categories
- update

### 📋 Other Changes
- Add auto-zero functionality for stale vehicle metrics
- build
- fix
- trigger pipeline
- fix missing /
- fix mkdocs site URL
- handle base route
- use redirects not routes
- add www route
- fix route


## [0.3.2] - 2025-07-28


### 🐛 Bug Fixes
- update GSM signal scaling from 0-31 to 1-5 range


## [0.3.1] - 2025-07-28


### 🐛 Bug Fixes
- handle None values in trip end positions
- improve error handling and trip parsing resilience

### 🧰 Maintenance
5cbd6fc chore(deps): downgrade homeassistant-stubs and update pymdown-extensions
773d192 chore(deps): update dependency homeassistant-stubs to v2025.7.4

### 📋 Other Changes
- Merge remote-tracking branch 'origin/renovate/homeassistant-stubs-2025.x'
- enhance(autopi): improve event handling and categorization


## [0.3.0] - 2025-07-28


### 🚗 Vehicle Features
- firing events on startup to avoid replaying old events


## [0.2.1] - 2025-07-28


### 📋 Other Changes
- Add fleet alerts and device events functionality
- Add trip tracking functionality to AutoPi integration
- Update README.md
- add logo


## [0.2.0] - 2025-07-28


### 🚗 Vehicle Features
- add error and abort messages to AutoPi strings
- Add API key update functionality to options flow

### 🐛 Bug Fixes
- improve versioning logic and remove redundant UI text
- improve git commit handling and code formatting
- name
- improve GitHub workflows for authentication and reliability
- update authentication method from Bearer to APIToken

### 🧰 Maintenance
2838042 refactor: replace position API with data fields API for richer vehicle metrics
55448a5 chore: docs
63974d6 chore: change project license from MIT to Apache-2.0
560f8ef ci: enhance GitHub Actions security and variable handling
87d0558 ci: add GitHub workflows and repository configuration

### 📚 Documentation
- fix documentation links and update Cloudflare deployment

### 📋 Other Changes
- Add vehicle position tracking with tiered update intervals
- Add AutoPi API documentation for Home Assistant integration
- Add pre-commit hooks and code quality tools
- Implement initial AutoPi Home Assistant integration
- initial commit
- Initial commit


---

For releases prior to v0.2.0, see the [GitHub Releases page](https://github.com/rknightion/autopi-ha/releases).
