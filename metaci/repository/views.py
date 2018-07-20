import hmac
import json
import re

from hashlib import sha1

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from metaci.repository.models import Branch
from metaci.repository.models import Repository
from metaci.plan.models import Plan
from metaci.build.models import Build
from metaci.build.utils import view_queryset

def repo_list(request, owner=None):
    repos = Repository.objects.all()

    if not request.user.is_staff:
        repos = repos.filter(public = True)
    if owner:
        repos = repos.filter(owner = owner)

    repo_list = []
    columns = []
       
    for repo in repos:
        repo_info = {}
        repo_info['name'] = repo.name
        repo_info['owner'] = repo.owner
        repo_info['title'] = unicode(repo)
        repo_info['build_count'] = repo.builds.count()
        repo_info['columns'] = {}
        for plan in repo.plans.filter(dashboard__isnull = False):
            if plan.name not in columns:
                columns.append(plan.name)
            builds = []
            latest_builds = plan.builds.filter(repo=repo).order_by('-time_queue')
            if plan.dashboard == 'last':
                builds.extend(latest_builds[:1])
            elif plan.dashboard == 'recent':
                builds.extend(latest_builds[:5])
            if builds:
                repo_info['columns'][plan.name] = builds
        repo_list.append(repo_info)

    columns.sort()

    for repo in repo_list:
        repo_columns = []
        for column in columns:
            repo_columns.append(repo['columns'].get(column))
        repo['columns'] = repo_columns

    context = {
        'repos': repo_list,
        'columns': columns,
    }
    print context
    return render(request, 'repository/repo_list.html', context=context)

def repo_detail(request, owner, name):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)

    query = {'repo': repo}
    builds = view_queryset(request, query)
    context = {
        'repo': repo,
        'builds': builds,
    }
    return render(request, 'repository/repo_detail.html', context=context)

def repo_branches(request, owner, name):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)

    context = {
        'repo': repo,
    }
    return render(request, 'repository/repo_branches.html', context=context)

def repo_plans(request, owner, name):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)

    context = {
        'repo': repo,
    }
    return render(request, 'repository/repo_plans.html', context=context)

@staff_member_required
def repo_orgs(request, owner, name):
    query = {
        'owner': owner,
        'name': name,
    }
    repo = get_object_or_404(Repository, **query)

    context = {
        'repo': repo,
    }
    return render(request, 'repository/repo_orgs.html', context=context)

def branch_detail(request, owner, name, branch):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)

    branch = get_object_or_404(Branch, repo=repo, name=branch)
    query = {'branch': branch}
    builds = view_queryset(request, query)
    context = {
        'branch': branch,
        'builds': builds,
    }
    return render(request, 'repository/branch_detail.html', context=context)

def commit_detail(request, owner, name, sha):
    query = {
        'owner': owner,
        'name': name,
    }
    if not request.user.is_staff:
        query['public'] = True
    repo = get_object_or_404(Repository, **query)
    
    query = {'commit': sha, 'repo': repo}
    builds = view_queryset(request, query)

    context = {
        'repo': repo,
        'builds': builds,
        'commit': sha,
    }
    return render(request, 'repository/commit_detail.html', context=context)

def validate_github_webhook(request):
    key = settings.GITHUB_WEBHOOK_SECRET
    signature = request.META.get('HTTP_X_HUB_SIGNATURE').split('=')[1]
    if type(key) == unicode:
        key = key.encode()
    mac = hmac.new(key, msg=request.body, digestmod=sha1)
    if not hmac.compare_digest(mac.hexdigest(), signature):
        return False
    return True

@csrf_exempt
@require_POST
def github_push_webhook(request):
    if not validate_github_webhook(request):
        return HttpResponseForbidden

    push = json.loads(request.body)
    repo_id = push['repository']['id']
    try:
        repo = Repository.objects.get(github_id = repo_id)
    except Repository.DoesNotExist:
        return HttpResponse('Not listening for this repository')
   
    branch_ref = push.get('ref')
    if not branch_ref:
        return HttpResponse('No branch found')

    branch_name = None
    if branch_ref.startswith('refs/heads/'):
        branch_name = branch_ref.replace('refs/heads/','')
    elif branch_ref.startswith('refs/tags/'):
        branch_name = branch_ref.replace('refs/tags/', 'tag: ')

    if branch_name:
        branch, created = Branch.objects.get_or_create(repo=repo, name=branch_name)
        if branch.is_removed:
            # resurrect the soft deleted branch
            branch.is_removed = False
            branch.save()

    for plan in repo.plans.filter(type__in=['commit', 'tag'], active=True, planrepository__active=True):
        run_build, commit, commit_message = plan.check_push(push)
        if run_build:
            build = Build(
                repo = repo,
                plan = plan,
                commit = commit,
                commit_message = commit_message,
                branch = branch,
                build_type = 'auto',
            )
            build.save() 

    return HttpResponse('OK')
