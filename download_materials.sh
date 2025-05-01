#!/bin/bash

# Default values
PORT=40711
REMOTE_HOST="root@93.114.160.254"
REMOTE_BASE_PATH="/workspace/VLMaterial/llava_hf/results"
LOCAL_DEST_PATH="$HOME/Downloads"

# Help message
show_help() {
    echo "Usage: $0 [options]"
    echo "Automate downloading material results from remote server"
    echo ""
    echo "Options:"
    echo "  -m, --model MODEL    Model name (e.g., llava-llama3-8b-sllm-p10)"
    echo "  -e, --epoch EPOCH    Epoch number (e.g., epoch5)"
    echo "  -i, --id ID          Material ID or pattern (e.g., 000 or '00*')"
    echo "  -d, --dest PATH      Local destination path (default: ~/Downloads)"
    echo "  -p, --port PORT      SSH port (default: 40711)"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Example: $0 -m llava-llama3-8b-sllm-p10 -e epoch5 -i '000*'"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -e|--epoch)
            EPOCH="$2"
            shift 2
            ;;
        -i|--id)
            ID="$2"
            shift 2
            ;;
        -d|--dest)
            LOCAL_DEST_PATH="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check required parameters
if [ -z "$MODEL" ] || [ -z "$EPOCH" ] || [ -z "$ID" ]; then
    echo "Error: Missing required parameters"
    show_help
    exit 1
fi

# Construct remote path
REMOTE_PATH="${REMOTE_BASE_PATH}/${MODEL}/eval-${EPOCH}/${ID}"

# Create local directory if it doesn't exist
mkdir -p "${LOCAL_DEST_PATH}"

# Display information
echo "Downloading from: ${REMOTE_HOST}:${REMOTE_PATH}"
echo "To: ${LOCAL_DEST_PATH}"
echo "Using port: ${PORT}"

# Start SSH agent and add key if not already running
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval $(ssh-agent)
    ssh-add
fi

# Execute the scp command
scp -P $PORT -r "${REMOTE_HOST}:${REMOTE_PATH}" "${LOCAL_DEST_PATH}/"

echo "Download complete!" 