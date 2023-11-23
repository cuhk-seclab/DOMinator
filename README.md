# DOMinator

## Overview
DOMinator is a innovative security mechanism designed to provide fine-grained confidentiality and integrity protection for sensitive client-side user data. 
It empowers web developers to effectively restrict the privileges of third-party scripts, while imposing minimal runtime overhead.

DOMinator is implemented on Chromium (version 88.0.4303.1).

### Code Structure
`patch/`: The patch of DOMinator implemetation.  
`labeling_tool/`: Extension code of the Labeling Tool.  
`policy_generator/`: The scripts of generating policies, updaing policies and automating browsers for log collection and evaluation.  
`policy_data/`: The policies generated for the 50 popular websites.   
`build_DOMinator.sh`: Building script.  
`rank2domain`: The list of the selected 50 websites.  

## Build
```
# Install depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH=$PATH:/path/to/depot_tools

# Build Chromium and apply patch
./build_DOMinator.sh
```

## Publication
You can find more details in our CCS 2023 paper:

**Fine-Grained Data-Centric Content Protection Policy for Web Applications**

```bibtex
@inproceedings{wang2023dominator,
author = {Wang, Zilun and Meng, Wei and Lyu, Michael R.},
title = {Fine-Grained Data-Centric Content Protection Policy for Web Applications},
year = {2023},
url = {https://doi.org/10.1145/3576915.3623217},
booktitle = {Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security},
}
```

## Credits
Some code of the DOMinator patch is based on [Mingxue Zhang/JSIsolate](https://github.com/cuhk-seclab/JSIsolate).  
The Labeling Tool builds upon the work of [p2c2e/aardvark2](https://github.com/p2c2e/aardvark2) and [ericclemmons/unique-selector](https://github.com/ericclemmons/unique-selector/).

We sincerely appreciate their valuable contributions and inspirational input in developing specific aspects of our project.

## Contacts
- Zilun Wang (<zlwang22@cse.cuhk.edu.hk>)
- Wei Meng (<wei@cse.cuhk.edu.hk>)
- Michael R. Lyu (<lyu@cse.cuhk.edu.hk>)
