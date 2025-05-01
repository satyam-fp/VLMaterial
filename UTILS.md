
1. Run the script with required parameters:

```bash
./download_materials.sh -m llava-llama3-8b-sllm-p10 -e epoch5 -i "000-stacked_stone-again-again-material-1"

```

2. For multiple materials, you can use wildcards:

```bash
./download_materials.sh -m llava-llama3-8b-sllm-p10 -e epoch5 -i "000*"
```

3. To change the download location:

```bash
./download_materials.sh -m llava-llama3-8b-sllm-p10 -e epoch5 -i "000*" -d ~/Documents/materials
```


## Any
```bash
scp -P 40711 -r root@93.114.160.254:/workspace/VLMaterial/llava_hf/results/llava-llama3-8b-sllm-p10/eval-epoch5/000-stacked_stone-again-again-material-1 ~/Downloads/
```