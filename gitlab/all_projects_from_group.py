"""
Get all projects from a Gitlab group and all its subgroups.

Requires:
    python-gitlab
"""
from gitlab import Gitlab
from pprint import pprint

TOKEN = "<API_TOKEN>"
URL = "<GITLAB URL>"
GROUP = "<GROUP NAME OR ID>"
FILTER_OUT_ARCHIVED = True

gl = Gitlab(URL, TOKEN)
group = gl.groups.get(GROUP)

# The subgroups here are of the GroupSubgroup GroupProject kind.
# We probably need the real thing, hence the get-by-id.
group_subgroups = [gl.groups.get(subgroup.id) for subgroup in group.descendant_groups.list(all=True)]
group_projects = list(group.projects.list(all=True))
for subgroup in group_subgroups:
    group_projects.extend(subgroup.projects.list(all=True))

if FILTER_OUT_ARCHIVED:
   group_projects = [p for p in group_projects if not p.archived]

projects = {p.name_with_namespace: gl.projects.get(p.id) for p in group_projects}

pprint(projects)
