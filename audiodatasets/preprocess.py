"""Download and convert 3 major data-sets for voice dictation

LibriSpeech, TEDLIUM_release2 and VCTK

The 3 Data-sets here required around 100GB of downloads, so
the idea of this module is that you'll download the dataset 
once and then use it for many experiments.
"""
import os
import time
import subprocess
import logging
import tempfile
import contextlib
from .corpora import build_corpora
from .baseoptions import get_options
log = logging.getLogger(__name__)

def _run_pipes_to_finish(pipes):
    while pipes:
        pipes = [
            pipe for pipe in pipes
            if pipe.poll() is None
        ]
        log.info("%s downloads running", len(pipes))
        time.sleep(5)
@contextlib.contextmanager
def chdir(directory):
    cwd = os.getcwd()
    os.chdir(directory)
    yield directory
    os.chdir(cwd)


def download_files(to_download):
    pipes = []
    for struct in to_download:
        dirname = os.path.dirname(struct['filename'])
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        log.info("Downloading %s => %s", struct['url'], struct['filename'])
        command = [
            'wget', 
                '-O', struct['filename'],
                '-o', struct['filename']+'.download.log',
                struct['url']
        ]
        if struct.get('start'):
            command.insert(1, '--continue')
        log.info("Command: %s", " ".join(command))
        pipes.append(subprocess.Popen(command))
    _run_pipes_to_finish(pipes)

def unpack_downloads(to_unpack, target):
    with chdir(target):
        pipes = []
        for unpack in to_unpack:
            pipes.append(subprocess.Popen([
                'tar', '-xf', unpack['filename'],
            ]))
        _run_pipes_to_finish(pipes)


def download(dry_run=False):
    """Download main operation"""
    logging.basicConfig(level=logging.INFO)
    parser = get_options('Downloads common spoken-text datasets')
    parser.add_argument(
        '--dry-run',
        default=False,
        action='store_true',
        help="If specified, just print out what would be downloaded and exit"
    )
    options = parser.parse_args()
    log.info("Download starting")
    _download(
        options.directory,
        build_corpora(options.directory, options.corpus),
        dry_run=options.dry_run,
    )
    log.info("Download complete")
    return 0


def _download(target, corpora, dry_run=False):
    """Shared downloading operation"""
    to_download = []
    for corpus in corpora:
        to_download += list(corpus.to_download())
    if dry_run:
        total = 0
        for struct in to_download:
            log.info("Would download %s => %s",
                     struct['url'], struct['filename'])
            total += (struct['expected_size'] - struct.get('start', 0))
        formatted_size = total // (1024 * 1024)
        log.info("Total to download: %sMB", formatted_size)
        return
    if to_download:
        download_files(to_download)
    for corpus in corpora:
        to_unpack = list(corpus.to_unpack())
        if to_unpack:
            import ipdb;ipdb.set_trace()
            unpack_downloads(to_unpack, corpus.local_dir)

def preprocess():
    """Main-function for the preprocessing operation"""
    logging.basicConfig(level=logging.INFO)
    parser = get_options(
        'Downloads and preprocesses common spoken-text datasets')
    options = parser.parse_args()
    target = options.directory
    corpora = build_corpora(target, options.corpus)
    log.info("Download starting for %s", corpora)
    _download(target, corpora)
    log.info("MFCC extraction starting")
    utterances = []
    for corpus in corpora:
        utterances += list(corpus.mfcc_utterances())
    log.info("MFCC extraction complete")
    return 0
