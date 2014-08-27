import argparse
import threading

from fuse import FUSE

from gitfs.utils import Args
from gitfs.routes import routes
from gitfs.router import Router
from gitfs.worker import MergeQueue, MergeWorker, FetchWorker


parser = argparse.ArgumentParser(prog='GitFS')
parser.add_argument('remote_url', help='repo to be cloned')
parser.add_argument('mount_point', help='where the repo should be mount')
parser.add_argument('-o', help='other options: repos_path, user, ' +
                               'group, branch, max_size, max_offset')
args = Args(parser)


# initialize merge queue
merge_queue = MergeQueue()
merging = threading.Event()

# setting router
router = Router(remote_url=args.remote_url,
                mount_path=args.mount_point,
                repos_path=args.repos_path,
                branch=args.branch,
                user=args.user,
                group=args.group,
                max_size=args.max_size,
                max_offset=args.max_offset,
                merge_queue=merge_queue,
                merging=merging)

# register all the routes
router.register(routes)

# setup workers
merge_worker = MergeWorker(args.author_name, args.author_email,
                           args.commiter_name, args.commiter_email,
                           merging, merge_queue, router.repo, args.upstream,
                           args.branch)
fetch_worker = FetchWorker("origin", args.branch, router.repo, merging)

merge_worker.start()
fetch_worker.start()

# ready to mount it
FUSE(router, args.mount_point, foreground=args.foreground, nonempty=True,
     allow_root=args.allow_root, allow_other=args.allow_other)
