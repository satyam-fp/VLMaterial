# Enhanced Logging System for VLMaterial

This document describes the enhanced logging system implemented for the VLMaterial project to track the generation and rendering flow.

## Overview

The enhanced logging system provides detailed, structured logs of the entire material generation and rendering process. It captures key events, timing information, errors, and success rates throughout the execution flow.

## Logging Functions

The system includes two primary logging functions:

1. **log_info**: Simple text-based logging
   ```python
   log_info(log_path, message, print_stdout=False)
   ```

2. **log_event**: Enhanced structured logging with timestamps and metadata
   ```python
   log_event(log_path, event_type, step, message, metadata=None, print_stdout=True)
   ```

### Parameters:

- `log_path`: Path to the log file
- `event_type`: Category of the event (e.g., 'MODEL_LOAD', 'GENERATION', 'RENDERING')
- `step`: Specific step within the event type (e.g., 'START', 'COMPLETE', 'ERROR')
- `message`: Human-readable description of the event
- `metadata`: Optional dictionary containing additional structured data
- `print_stdout`: Whether to also print the message to standard output

## Log Structure

The enhanced logs using `log_event` are stored as JSON objects with the following structure:

```json
{
  "timestamp": "2023-10-24 13:45:32.123",
  "event_type": "GENERATION",
  "step": "START",
  "message": "Starting generation for sample 42",
  "metadata": {
    "batch_size": 4,
    "max_new_tokens": 2048,
    "temperature": 1.0
  }
}
```

## Event Types

The system uses standardized event types to categorize different parts of the process:

- `MAIN`: Main process events
- `INFERENCE`: Overall inference process events
- `DATASET`: Dataset loading and processing
- `MODEL`: Model loading and configuration
- `HARDWARE`: Device and hardware information
- `SAMPLE`: Sample-level processing events
- `BATCH`: Batch processing events
- `GENERATION`: Text generation events
- `DECODE`: Token decoding events
- `RESPONSE`: Generated response handling
- `VERIFY`: Verification process events
- `RENDER`: Blender rendering events
- `CODE`: Code extraction and processing
- `IMAGE`: Image loading and saving
- `PROCESS`: Process management events
- `PROGRESS`: Progress updates
- `QUEUE`: Queue management
- `ERROR`: Error events

## Common Steps

Standard steps used across different event types:

- `INIT`, `START`, `PREP`: Beginning of a process
- `LOADING`, `LOADED`, `COMPLETE`: Process progression
- `SUCCESS`, `FAILED`, `ERROR`: Process outcomes
- `EXIT`, `STOP`: Termination events

## Log Analysis

A log analyzer script is provided to visualize and report on the logging data:

```bash
python log_analyzer.py [log_path] --output-dir [output_directory]
```

The analyzer produces:

1. Statistical analysis of generation and rendering times
2. Error type distribution
3. Success rates for each sample
4. Timeline visualization of the entire process
5. A comprehensive text report

## Example Outputs

The log analyzer generates:

1. `time_histograms.png`: Distribution of generation and rendering times
2. `error_types.png`: Bar chart of error types
3. `success_rates.png`: Success rates by sample
4. `timeline.png`: Timeline visualization of events
5. `analysis_report.txt`: Detailed text report

## Integration with Existing Code

The logging system is integrated throughout the inference process:

1. In the main process to track overall execution
2. In the model loading and dataset preparation phases
3. During the generation loop for each batch
4. During the verification and rendering steps
5. For error handling and reporting

## Usage Example

```python
from utils import log_event

# At the start of processing a sample
log_event(log_path, "SAMPLE", "START", f"Processing sample {idx}", {
    "sample_id": source['id'],
    "image": source.get('image', None)
})

# When generation is complete
log_event(log_path, "GENERATION", "COMPLETE", "Generation complete", {
    "output_seq_length": outputs.sequences.shape[1]
})

# When an error occurs
log_event(log_path, "RENDER", "ERROR", "Render failed", {
    "error_type": "timeout",
    "timeout_seconds": 120
})
```

## Extending the System

To add logging for new components:

1. Import the logging functions from utils
2. Choose appropriate event types and steps
3. Include relevant metadata
4. Call `log_event` at key points in your code 

`python llava_hf/log_analyzer.py /workspace/VLMaterial/llava_hf/results/llava-llama3-8b-sllm-p10/eval-epoch5/inference_stdout.log --output-dir analysis_inference`

`python llava_hf/log_analyzer.py /workspace/VLMaterial/llava_hf/results/llava-llama3-8b-sllm-p10/eval-epoch5/main.log --output-dir analysis_main`