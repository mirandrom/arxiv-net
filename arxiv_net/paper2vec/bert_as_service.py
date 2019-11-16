from bert_serving.server.helper import get_args_parser
from bert_serving.server import BertServer
from bert_serving.client import BertClient
from pathlib import Path
from typing import List

import os
"""
usage: bert-serving-server [-h] -model_dir MODEL_DIR 
                           [-tuned_model_dir TUNED_MODEL_DIR]
                           [-ckpt_name CKPT_NAME] Default: “bert_model.ckpt”
                           [-config_name CONFIG_NAME] Default: “bert_config.json”
                           [-graph_tmp_dir GRAPH_TMP_DIR]
                           [-max_seq_len MAX_SEQ_LEN] Default: 25
                           [-cased_tokenization] Default: True
                           [-pooling_layer POOLING_LAYER [POOLING_LAYER ...]] Default: [-2]
                           [-pooling_strategy {NONE,REDUCE_MAX,REDUCE_MEAN,REDUCE_MEAN_MAX,FIRST_TOKEN,LAST_TOKEN}] Default: REDUCE_MEAN
                           [-mask_cls_sep] Default: False
                           [-show_tokens_to_client] Default: False
                           [-port PORT] Default: 5555
                           [-port_out PORT_OUT] Default: 5556
                           [-http_port HTTP_PORT]
                           [-http_max_connect HTTP_MAX_CONNECT] Default: 10
                           [-cors CORS] Default: “*”
                           [-num_worker NUM_WORKER] Default: 1
                           [-max_batch_size MAX_BATCH_SIZE] Default: 256
                           [-priority_batch_size PRIORITY_BATCH_SIZE] Default: 16
                           [-cpu] Default: False
                           [-xla] Default: False
                           [-fp16] Default: False
                           [-gpu_memory_fraction GPU_MEMORY_FRACTION] Default: 0.5
                           [-device_map DEVICE_MAP [DEVICE_MAP ...]] Default: []
                           [-prefetch_size PREFETCH_SIZE] Default: 10 (0 for CPU)
                           [-fixed_embed_length] Default: False
                           [-verbose] Default: False
                           [-version] 
"""


def run_server(out_dir = "../bas_out",
               max_seq_len=128,
               num_workers=4,
               max_batch_size=64,
               ):
    model_dir = (Path(__file__).parent / "uncased_L-12_H-768_A-12").absolute()
    print(f"Loading BERT from {model_dir}")
    bert_server_args = get_args_parser().parse_args([
                                         '-model_dir', str(model_dir),
                                         '-max_seq_len', str(max_seq_len),
                                         # '-pooling_strategy', 'REDUCE_MEAN_MAX',
                                         '-num_worker', str(num_workers),
                                         '-max_batch_size', str(max_batch_size),
                                         '-port', '5555',
                                         '-port_out', '5556',
                                         '-mask_cls_sep',
                                         '-cpu',
                                         ])
    if not os.path.exists(out_dir):
        print(f"Creating directory {out_dir} for ZeroMQ logs")
        os.makedirs(out_dir)
    os.environ['ZEROMQ_SOCK_TMP_DIR'] = out_dir
    print("Starting BERT Server")
    server = BertServer(bert_server_args)
    server.start()


def run_client():
    print("Starting BERT Client")
    bc = BertClient(timeout=30_000)
    return bc
