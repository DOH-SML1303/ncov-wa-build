This is a [Nextstrain](https://nextstrain.org) build for novel coronavirus (nCoV), visible at [nextstrain.org/ncov](https://nextstrain.org/ncov).

## Data

The Wuhan coronavirus genomes were generously shared by scientists at the Shanghai Public Health Clinical Center & School of Public Health, Fudan University (sample *WH-Human_1*) via this [post on virological.org](http://virological.org/t/initial-genome-release-of-novel-coronavirus/319), and by scientists at the National Institute for Viral Disease Control and Prevention, China CDC (samples *BetaCoV/Wuhan/IVDC-HB-01/2019*, *BetaCoV/Wuhan/IVDC-HB-05/2019*, *BetaCoV/Wuhan/IVDC-HB-04/2020*) at the Institute of Pathogen Biology, Chinese Academy of Medical Sciences & Peking Union Medical College (sample *BetaCoV/Wuhan/IPBCAMS-WH-01/2019*), at the Wuhan Institute of Virology, Chinese Academy of Sciences (sample *BetaCoV/Wuhan/WIV04/2019*) and at the Department of Medical Sciences, National Institute of Health, Nonthaburi, Thailand (samples ) via [GISAID](https://gisaid.org). We gratefully acknowledgement their contributions.

Background data for this build was sourced [from Genbank via VIPR](https://www.viprbrc.org/brc/vipr_genome_search.spg?method=ShowCleanSearch&decorator=corona). Here, we downloaded all the SARS-like coronaviruses that were more than 5000 bases in length. These sequences are available in the repo at `data/sequences.fasta`.

Novel coronaviruses from Wuhan are not included as part of this repo as many of them are protected by the terms of GISAID sharing. Here, these 6 genomes will need to be supplemented by the user. Please add these as additional strains in `data/sequences.fasta`. Metadata for these 6 viruses already exists in `data/metadata.tsv`.

## Building

After provisioning the `data/sequences.fasta` file, the entire build can be regenerated by running
```
snakemake -p
```
with a [local Nextstrain installation](https://nextstrain.org/docs/getting-started/local-installation) or by running
```
nextstrain build .
```
with a [containerized Nextstrain installation](https://nextstrain.org/docs/getting-started/container-installation).

The resulting output JSON at `auspice/ncov.json` can be visualized by running `auspice view --datasetDir auspice` or `nextstrain view auspice/` depending on local vs containerized installation.

## Notes

There were 5 SNPs present in the Wuhan samples in the first 11 bases of the alignment that are masked with `N` in the pipeline (via rule `mask`) as likely sequencing artifacts. Additionally, sample BetaCoV/Wuhan/IVDC-HB-05/2019 may have sequencing artifacts that make it appear more diverged than it actually is.
