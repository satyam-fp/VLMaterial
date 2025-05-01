# MIT License
# Copyright (c) 2025 Massachusetts Institute of Technology
# See the LICENSE file for full license details.

import os
import os.path as osp
import sys

# Align CUDA device order with X server
os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'

sys.path.append(osp.dirname(osp.abspath(__file__)))

from dataclasses import dataclass, field
from torch.multiprocessing import Process, Queue, set_start_method
from PIL import Image
import os
import subprocess

from transformers import HfArgumentParser, AutoProcessor
from tqdm import tqdm
import torch

from dataset import DataArguments, MaterialDataset
from model import load_pretrained_model
from utils import SYSTEM_PROMPT_LLAVA, log_info, check_stdout, log_event


ROOT_DIR = osp.dirname(osp.dirname(osp.abspath(__file__)))
SCRIPTS_DIR = osp.join(ROOT_DIR, 'data_scripts')


@dataclass
class Arguments:
    '''Arguments for LLM inference.
    '''
    # I/O
    test_data_path: str
    output_dir: str

    # Model configuration
    model_path: str | None = None
    model_base: str = 'llava-hf/llama3-llava-next-8b-hf'
    display_id: int = 0
    device_id: list[int] = field(default_factory=list)

    # Dataset-related info
    blender_path: str = osp.join(ROOT_DIR, 'infinigen', 'blender', 'blender')
    image_folder: str = osp.join(ROOT_DIR, 'material_dataset_filtered_v2')
    info_dir: str = osp.join(ROOT_DIR, 'material_dataset_info')
    data_format: str = 'v1.5'

    # Inference settings
    mode: str = 'all'                   # Inference mode (generation, verification, or both)
    num_processes: int = 1              # Number of processes for parallel inference
    num_samples: int = 4                # Target number of samples to generate
    max_samples: int = 20               # Maximum number of trials
    max_length: int = 2048              # Maximum token sequence length
    batch_size: int | None = None       # Batch size for inference
    temperature: float = 1.0
    top_k: int = 10
    top_p: float = 0.9
    min_file_size: int = 12000          # Minimum file size for rendered material images


def response_to_code(response: str) -> str:
    '''Extract code block delimited by triple backticks from the response.
    '''
    code = response.strip()
    if "```" in code:
        code = code[code.index("```") + 3:]
    if code.startswith("python"):
        code = code[6:]
    if "```" in code:
        code = code[:code.index("```")]
    return code


def verify_program(
        response: str, args: Arguments, target_id: int, sample_id: int, example_dir: str, stdout_path: str,
        min_file_size: int = 12000, display_id: int | None = None, device_id: int | None = None
    ) -> bool:
    '''Verify the generated response and save the program if successful.
    '''
    # Define temporary file paths
    code_path = osp.join(example_dir, 'temp_full.py')
    render_path = osp.join(example_dir, 'temp_render.jpg')

    log_event(stdout_path, "VERIFY", "START", f"Verifying sample {sample_id}", {
        "target_id": target_id,
        "example_dir": example_dir,
        "code_path": code_path,
        "render_path": render_path
    })

    # Clean up temporary files if any
    for f in os.listdir(example_dir):
        if f.startswith('temp_'):
            os.remove(osp.join(example_dir, f))

    # Extract the program from the response
    with open(code_path, "w") as f:
        f.write(response_to_code(response))
    
    log_event(stdout_path, "VERIFY", "CODE_EXTRACTED", f"Code extracted for sample {sample_id}", {
        "code_path": code_path,
        "code_size": osp.getsize(code_path)
    })

    # Render the code to an image
    display_name = f':{display_id if display_id is not None else 0}'
    display_name += f'.{device_id}' if device_id is not None else ''
    render_kwargs = {
        'capture_output': True,
        'text': True,
        'env': {'DISPLAY': display_name},
        'timeout': 120
    }

    log_event(stdout_path, "RENDER", "START", f"Starting render for sample {sample_id}", {
        "display": display_name,
        "blender_path": args.blender_path
    })

    try:
        # log all the parameters
        log_event(stdout_path, "RENDER", "PARAMS", f"Render parameters for sample {sample_id}", {
            "blender_path": args.blender_path,
            "script_path": osp.join(SCRIPTS_DIR, 'render.py'),
            "code_path": code_path,
            "info_dir": args.info_dir,
            "render_path": render_path,
            "render_kwargs": render_kwargs
        })
        ret = subprocess.run([
            args.blender_path, '-b', '-P', osp.join(SCRIPTS_DIR, 'render.py'),
            '--', '-c', code_path, '-i', args.info_dir, '-o', render_path,
        ], **render_kwargs)
        
        if sample_id == 1:
            print(f"render return: {ret}")

    except subprocess.TimeoutExpired:
        log_info(stdout_path, f"Error when processing test case {sample_id}:\nRender timed out")
        log_event(stdout_path, "RENDER", "ERROR", f"Render timed out for sample {sample_id}", {
            "error_type": "timeout",
            "timeout_seconds": 120
        })
        return False

    # Check render result
    if check_stdout(ret.stdout, render_path, sample_id, stdout_path):
        log_event(stdout_path, "RENDER", "ERROR", f"Render failed for sample {sample_id}", {
            "error_source": "stdout"
        })
        return False

    # Check the rendered image file size
    if osp.getsize(render_path) < min_file_size:
        log_info(stdout_path, f"Error when processing test case {sample_id}:\nRendered image too small")
        log_event(stdout_path, "RENDER", "ERROR", f"Rendered image too small for sample {sample_id}", {
            "error_type": "image_size",
            "actual_size": osp.getsize(render_path),
            "min_required": min_file_size
        })
        return False

    # Rename the generated files
    pred_name = f'pred_{target_id:05d}'
    os.rename(code_path, osp.join(example_dir, f'{pred_name}_full.py'))
    os.rename(render_path, osp.join(example_dir, f'{pred_name}_render.jpg'))
    
    log_event(stdout_path, "VERIFY", "SUCCESS", f"Sample {sample_id} successfully validated", {
        "target_id": target_id,
        "final_code_path": osp.join(example_dir, f'{pred_name}_full.py'),
        "final_render_path": osp.join(example_dir, f'{pred_name}_render.jpg')
    })

    return True


def run_inference(
        args: Arguments, rank: int, task_queue: Queue, result_queue: Queue
    ):
    '''Runs the inference process.
    '''
    stdout_path_inference = osp.join(args.output_dir, f'inference_stdout.log')
    open(stdout_path_inference, 'w').close()
    
    log_event(stdout_path_inference, "INFERENCE", "INIT", f"Starting inference process (rank {rank})", {
        "mode": args.mode,
        "output_dir": args.output_dir,
        "rank": rank,
        "model_path": args.model_path,
        "model_base": args.model_base
    })

    # Create a local dataset copy
    processor = AutoProcessor.from_pretrained(args.model_base)
    data_args = DataArguments(
        image_folder=args.image_folder,
        data_format=args.data_format
    )
    
    log_event(stdout_path_inference, "DATASET", "LOAD", "Loading dataset", {
        "test_data_path": args.test_data_path,
        "image_folder": args.image_folder,
        "data_format": args.data_format
    })
    
    dataset = MaterialDataset(
        args.test_data_path, processor, data_args, inference=True,
        zero_shot=args.model_path is None, system_prompt=SYSTEM_PROMPT_LLAVA
    )
    
    log_event(stdout_path_inference, "DATASET", "LOADED", f"Dataset loaded with {len(dataset)} samples")

    # PyTorch device
    devices = [f'cuda:{i}' for i in args.device_id]
    device = torch.device(devices[rank] if len(devices) > 1 else devices[0])
    log_info(stdout_path_inference, f"Mode: {args.mode}")
    log_info(stdout_path_inference, f"Using device: {device}")
    
    log_event(stdout_path_inference, "HARDWARE", "DEVICE", f"Using device: {device}", {
        "device_index": device.index if hasattr(device, 'index') else None,
        "device_type": device.type
    })

    # Load the pretrained model
    if args.mode in ('all', 'gen'):
        log_event(stdout_path_inference, "MODEL", "LOADING", "Loading model", {
            "model_path": args.model_path,
            "model_base": args.model_base
        })
        
        model = load_pretrained_model(args.model_path, args.model_base, device)
        model.generation_config.pad_token_id = processor.tokenizer.pad_token_id
        
        log_event(stdout_path_inference, "MODEL", "LOADED", "Model loaded successfully", {
            "model_type": type(model).__name__,
            "generation_config": {
                "max_length": args.max_length,
                "temperature": args.temperature,
                "top_k": args.top_k,
                "top_p": args.top_p
            }
        })
    else:
        model = None
        log_event(stdout_path_inference, "MODEL", "SKIPPED", "Model loading skipped (render-only mode)")
        
    # Main inference loop
    while True:
        # Get the next task index; break if the stop signal is received
        idx = task_queue.get()
        if idx < 0:
            log_event(stdout_path_inference, "INFERENCE", "STOP", "Received stop signal")
            break

        # Read the source data dictionary
        source = dataset.get_source(idx)
        
        log_event(stdout_path_inference, "SAMPLE", "START", f"Processing sample {idx}", {
            "sample_id": source['id'],
            "image": source.get('image', None)
        })

        # Create the output folder for this case
        example_dir = osp.join(args.output_dir, f"{idx:03d}" + "-" + source['id'])
        os.makedirs(example_dir, exist_ok=True)

        # Generation-mode preparation
        if args.mode in ('all', 'gen'):
            log_event(stdout_path_inference, "GENERATION", "PREP", f"Preparing for generation on sample {idx}", {
                "example_dir": example_dir
            })
            
            # Save input image and ground-truth code
            input_image = Image.open(osp.join(args.image_folder, source['image'])).convert('RGB')
            input_image.save(osp.join(example_dir, "input.jpg"))
            
            log_event(stdout_path_inference, "IMAGE", "SAVED", f"Input image saved for sample {idx}", {
                "image_path": osp.join(example_dir, "input.jpg"),
                "image_size": input_image.size
            })

            if len(source['conversation']) > 1:
                gt_code = source['conversation'][1]['content'][0]['text'].strip().strip('```')
                gt_code = gt_code[gt_code.index('\n') + 1:] if gt_code.startswith('python') else gt_code
                with open(osp.join(example_dir, "gt_full.py"), "w") as f:
                    f.write(gt_code)
                
                log_event(stdout_path_inference, "CODE", "GT_SAVED", f"Ground truth code saved for sample {idx}", {
                    "code_path": osp.join(example_dir, "gt_full.py"),
                    "code_size": len(gt_code)
                })

            # Move data to device and cast to the correct data type
            inputs = {k: v.to(device, non_blocking=True) for k, v in dataset[idx].items()}
            inputs = {
                k: v.to(model.dtype) if torch.is_floating_point(v) else v
                for k, v in inputs.items()
            }

        # Verification-mode preparation
        if args.mode in ('all', 'render'):
            log_event(stdout_path_inference, "VERIFICATION", "PREP", f"Preparing for verification on sample {idx}", {
                "example_dir": example_dir
            })
            
            # Create the stdout log file
            stdout_path = osp.join(example_dir, 'gen_programs_stdout.log')
            open(stdout_path, 'w').close()

        # Initialize the progress bar
        pbar = tqdm(
            total=args.max_samples if args.mode == 'gen' else args.num_samples,
            desc=osp.basename(example_dir),
            position=0
        )

        # Keep generating samples until reaching the user-specified number
        num_sampled, num_passed = 0, 0
        
        log_event(stdout_path_inference, "SAMPLE", "LOOP_START", f"Starting generation loop for sample {idx}", {
            "max_samples": args.max_samples,
            "target_num_passed": args.num_samples
        })

        while num_sampled < args.max_samples and num_passed < args.num_samples:
            # Calculate batch size
            batch_size = args.batch_size if args.batch_size is not None else args.num_samples
            batch_size = min(batch_size, args.max_samples - num_sampled)
            
            log_event(stdout_path_inference, "BATCH", "START", f"Processing batch for sample {idx}", {
                "batch_size": batch_size,
                "samples_so_far": num_sampled,
                "passed_so_far": num_passed
            })

            # Generate a batch of responses (included in mode 'all' or 'gen')
            if args.mode in ('all', 'gen'):
                # Create batched input
                batch_inputs = {
                    k: (
                        v.expand(batch_size, *v.shape[1:]) if v.shape[0] == 1
                        else v.repeat(batch_size, *([1] * (v.ndim - 1)))
                    ) 
                    for k, v in inputs.items()
                }
                
                log_event(stdout_path_inference, "GENERATION", "START", f"Generating samples for batch", {
                    "batch_size": batch_size,
                    "max_new_tokens": args.max_length,
                    "temperature": args.temperature
                })
                
                # Generate samples
                with torch.inference_mode():
                    outputs = model.generate(
                        **batch_inputs,
                        do_sample=args.temperature > 0,
                        max_new_tokens=args.max_length,
                        temperature=args.temperature,
                        top_k=args.top_k,
                        top_p=args.top_p,
                        use_cache=True,
                        return_dict_in_generate=True
                    )
                
                log_event(stdout_path_inference, "GENERATION", "COMPLETE", f"Generation complete for batch", {
                    "output_seq_length": outputs.sequences.shape[1]
                })
                
                # Check if the input tokens are correctly returned
                input_ids, output_ids = batch_inputs['input_ids'], outputs.sequences
                input_length = input_ids.shape[1]
                if not torch.equal(input_ids, output_ids[:, :input_length]):
                    error_msg = "Input tokens are not correctly returned."
                    log_event(stdout_path_inference, "GENERATION", "ERROR", error_msg, {
                        "error_type": "token_mismatch"
                    })
                    raise ValueError(error_msg)

                # Decode the generated samples
                log_event(stdout_path_inference, "DECODE", "START", "Decoding generated samples")
                responses = processor.batch_decode(output_ids[:, input_length:], skip_special_tokens=True)
                log_event(stdout_path_inference, "DECODE", "COMPLETE", "Decoding complete", {
                    "num_responses": len(responses)
                })

                # Save responses
                for i, response in enumerate(responses):
                    response_path = osp.join(example_dir, f'sample_{num_sampled + i:05d}_response.txt')
                    with open(response_path, 'w') as f:
                        f.write(response)
                    
                    log_event(stdout_path_inference, "RESPONSE", "SAVED", f"Response {num_sampled + i} saved", {
                        "response_path": response_path,
                        "response_length": len(response)
                    })

                    # Update the progress bar in generation-only mode
                    if args.mode == 'gen':
                        pbar.update(1)

                pbar.refresh()

            # Read responses from saved files if the mode is verification only
            else:
                log_event(stdout_path_inference, "RESPONSE", "LOADING", "Loading responses from files")
                responses = []
                for i in range(batch_size):
                    response_path = osp.join(example_dir, f'sample_{num_sampled + i:05d}_response.txt')
                    if osp.exists(response_path):
                        with open(response_path) as f:
                            responses.append(f.read())
                
                log_event(stdout_path_inference, "RESPONSE", "LOADED", "Responses loaded", {
                    "num_responses": len(responses)
                })
            
            # Verify the responses
            if args.mode in ('all', 'render'):
                log_event(stdout_path_inference, "VERIFICATION", "START", "Starting verification of responses")
                # Process each response
                for response in responses:
                    sample_result = verify_program(
                        response, args, num_passed, num_sampled, example_dir, stdout_path,
                        min_file_size=args.min_file_size, display_id=args.display_id,
                        device_id=device.index
                    )
                    
                    if sample_result:
                        pbar.update(1)
                        num_passed += 1
                        log_event(stdout_path_inference, "VERIFICATION", "PASSED", f"Sample {num_sampled} passed verification", {
                            "num_passed": num_passed,
                            "target": args.num_samples
                        })
                    else:
                        log_event(stdout_path_inference, "VERIFICATION", "FAILED", f"Sample {num_sampled} failed verification")
                    
                    num_sampled += 1

                    # Finish early if the desired number of samples is reached
                    if num_passed >= args.num_samples:
                        log_event(stdout_path_inference, "SAMPLE", "COMPLETE", f"Reached target number of passed samples for {idx}", {
                            "num_passed": num_passed,
                            "num_sampled": num_sampled
                        })
                        break

            # Otherwise, update the number of samples so that the iteration can continue
            else:
                num_sampled += batch_size
                log_event(stdout_path_inference, "GENERATION", "BATCH_COMPLETE", f"Batch complete for sample {idx}", {
                    "num_sampled": num_sampled,
                    "max_samples": args.max_samples
                })

        # Delete the temporary files if any
        for f in os.listdir(example_dir):
            if f.startswith('temp_'):
                os.remove(osp.join(example_dir, f))

        log_event(stdout_path_inference, "SAMPLE", "FINISHED", f"Finished processing sample {idx}", {
            "num_sampled": num_sampled,
            "num_passed": num_passed
        })
        
        # Update the result queue
        result_queue.put(idx)

    log_event(stdout_path_inference, "INFERENCE", "EXIT", f"Inference process (rank {rank}) exiting")


def main():
    # Parse command-line arguments
    hf_parser = HfArgumentParser(Arguments)
    args = hf_parser.parse_args_into_dataclasses()[0]
    
    # Create a main log file
    main_log_path = osp.join(args.output_dir, 'main.log')
    os.makedirs(args.output_dir, exist_ok=True)
    open(main_log_path, 'w').close()
    
    log_event(main_log_path, "MAIN", "START", "Starting the inference process", {
        "args": args.__dict__
    })

    # Check mode parameter
    if args.mode not in ('all', 'gen', 'render'):
        error_msg = f'Unknown inference mode: {args.mode}'
        log_event(main_log_path, "MAIN", "ERROR", error_msg, {
            "error_type": "invalid_mode",
            "mode": args.mode
        })
        raise ValueError(error_msg)

    # Create the dataset
    log_event(main_log_path, "DATASET", "LOADING", "Loading dataset")
    processor = AutoProcessor.from_pretrained(args.model_base)
    data_args = DataArguments(
        image_folder=args.image_folder,
        data_format=args.data_format
    )
    dataset = MaterialDataset(
        args.test_data_path, processor, data_args, inference=True,
        zero_shot=args.model_path is None, system_prompt=SYSTEM_PROMPT_LLAVA
    )
    log_event(main_log_path, "DATASET", "LOADED", f"Dataset loaded with {len(dataset)} samples")

    # Create the multi-processing queues
    task_queue = Queue()
    result_queue = Queue()

    # Insert tasks and stop signals
    for i in range(len(dataset)):
        task_queue.put(i)
    for _ in range(args.num_processes):
        task_queue.put(-1)
        
    log_event(main_log_path, "QUEUE", "SETUP", f"Task queue prepared with {len(dataset)} samples")

    # Spawn processes
    processes = []
    log_event(main_log_path, "PROCESS", "SPAWN", f"Spawning {args.num_processes} inference processes")
    for i in range(args.num_processes):
        p = Process(target=run_inference, args=(args, i, task_queue, result_queue))
        p.start()
        processes.append(p)
        log_event(main_log_path, "PROCESS", "STARTED", f"Process {i} started with PID {p.pid}")

    # Use a progress bar to monitor the total progress
    pbar = tqdm(total=len(dataset), desc='Inference', unit='images', position=0)
    while pbar.n < len(dataset):
        result_idx = result_queue.get()
        pbar.update()
        log_event(main_log_path, "PROGRESS", "UPDATE", f"Sample {result_idx} completed", {
            "completed": pbar.n,
            "total": len(dataset),
            "percent": round(pbar.n / len(dataset) * 100, 2)
        })

    # Wait for all processes to finish
    for i, p in enumerate(processes):
        p.join()
        log_event(main_log_path, "PROCESS", "JOINED", f"Process {i} finished")
        
    log_event(main_log_path, "MAIN", "COMPLETE", "Inference process completed successfully", {
        "total_samples": len(dataset),
        "output_dir": args.output_dir
    })


if __name__ == '__main__':
    set_start_method('spawn')
    main()
