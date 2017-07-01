import os
import subprocess

from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator

from django.apps import apps
from ansi2html import Ansi2HTMLConverter

from cumulusci.core.exceptions import CommandException

def paginate(build_list, request):
    page = request.GET.get('page')
    per_page = request.GET.get('per_page', '25')
    paginator = Paginator(build_list, int(per_page))
    try:
        builds = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        builds = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        builds = paginator.page(paginator.num_pages)
    return builds

def view_queryset(request, query=None, pagination=True):
    if not query:
        query = {}

    if not request.user.is_staff:
        query['plan__public'] = True

    Build = apps.get_model('build', 'Build')
    builds = Build.objects.all()
    if query:
        builds = builds.filter(**query)

    order_by = request.GET.get('order_by', '-time_queue')
    order_by = order_by.split(',')
    builds = builds.order_by(*order_by)
    if pagination:
        builds = paginate(builds, request)
    return builds

def format_log(log):
    conv = Ansi2HTMLConverter(dark_bg=False, scheme='solarized')
    headers = conv.produce_headers()
    content = conv.convert(log, full=False)
    content = '<pre class="ansi2html-content">{}</pre>'.format(content)
    #content = '<div class="body_foreground body_background">{}</div>'.format(content)
    return headers + content

    previous_dev_hub = ''.join(previous_dev_hub)
    previous_dev_hub = previous_dev_hub.strip()
    
def run_command(command, env=None, cwd=None):
    kwargs = {}
    if env:
        kwargs['env'] = env
    if cwd:
        kwargs['cwd'] = cwd
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        bufsize=1,
        shell=True,
        executable='/bin/bash',
        **kwargs
    )
    for line in iter(p.stdout.readline, ''):
        yield line
    p.stdout.close()
    p.wait()
    if p.returncode:
        message = 'Return code: {}\nstderr: {}'.format(
            p.returncode,
            p.stderr,
        )
        raise CommandException(message)
