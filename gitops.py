import yaml
import git
from git import RemoteProgress
import os

def loadConfig(configPath):
    with open('config.yml') as c:
        config = yaml.load(c, yaml.SafeLoader)
        return config

def repoCloned(path):
    return os.path.isdir(path)

def cloneRepo(url, branch, folder):
    return git.Repo.clone_from(url, folder, branch=branch)

def getRepoObj(folder):
    return git.Repo(folder)

def remoteAhead(repo_obj, branch):
    commits_diff = repo_obj.git.rev_list('--left-right', '--count', f'{branch}...{branch}@{{u}}')
    num_ahead, num_behind = commits_diff.split('\t')
    return int(num_ahead) > 0

def getValueFromVersionFile(version_file_path, key):
    with open(version_file_path) as f:
        lines = f.readlines()
        for line in lines:
            if(key in line):
                l = line.split('"')[1::2]
                return l[0]

def updateValueInVerionFile(version_file_path, key, oldValue, newValue):
    with open(version_file_path) as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            if(key in line):
                lines[index] = line.replace(oldValue, newValue)
    
    with open(version_file_path, 'w') as f:
        f.writelines(lines)

def incrementVersion(old_version):
    parts = old_version.split('.')
    last_part_index = len(parts)-1
    last_part = int(parts[last_part_index]) + 1
    parts[last_part_index] = str(last_part)
    return ".".join(parts)

def commitAndPushRepo(repo_path, message):
    repoObj = git.Repo(repo_path)
    repoObj.index.commit(message)
    origin = repoObj.remote(name='origin')
    origin.push()
    


