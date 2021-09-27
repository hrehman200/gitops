import yaml
import git
import os
import zipfile
from shutil import copyfile
import xml.etree.ElementTree as ET
import logging
import subprocess

log = logging.Logger(__name__)

def loadConfig(configPath):
    with open('config.yml') as c:
        config = yaml.load(c, yaml.SafeLoader)
        return config

def setLogging(log_file_path):
    global log
    logging.basicConfig(format='[%(asctime)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO,
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ])
    log = logging.getLogger(__name__)
    log.info('################################################################')
    log.info('Setting logging')
    log.info('################################################################')
    return log

def repoCloned(path):
    global log
    try:
        cloned = os.path.isdir(path)
        log.info(f"""Repo {path} exists : {cloned}""")
        return cloned
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")

def cloneRepo(url, branch, folder):
    global log
    try:
        log.info(f"""Cloning repo {url} {branch} to dir {folder} """)
        return git.Repo.clone_from(url, folder, branch=branch)
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")


def pullRepo(repo_path):
    global log
    try:
        log.info(f"""Pulling repo {getRepoName(repo_path)} """)
        repo = git.Repo(repo_path)
        o = repo.remotes.origin
        o.pull()
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")

def getRepoHash(repo_path):
    try:
        repo = git.Repo(repo_path)
        sha = repo.head.object.hexsha
        return sha
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")

def getRepoObj(folder):
    try:
        return git.Repo(folder)
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")

def getRepoName(repo_path):
    try:
        repo = git.Repo(repo_path)
        return repo.remotes.origin.url.split('.git')[0].split('/')[-1]
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")

def remoteAhead(repo_path, branch):
    global log
    try:
        repo_obj = git.Repo(repo_path)
        for remote in repo_obj.remotes:
            remote.fetch()
        commits_diff = repo_obj.git.rev_list('--left-right', '--count', f'{branch}...{branch}@{{u}}')
        num_ahead, num_behind = commits_diff.split('\t')
        ahead = int(num_ahead) > 0
        log.info(f"""Repo {getRepoName(repo_path)} is ahead? : {ahead}""")
        return ahead
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")

def getValueFromVersionFile(version_file_path, key):
    global log
    with open(version_file_path) as f:
        lines = f.readlines()
        for line in lines:
            if(key in line):
                l = line.split('"')[1::2]
                return l[0]

def updateValueInVerionFile(version_file_path, key, oldValue, newValue):
    global log
    with open(version_file_path) as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            if(key in line):
                log.info(f"""Updating {key} to : {newValue}""")
                lines[index] = line.replace(oldValue, newValue)
    
    with open(version_file_path, 'w') as f:
        f.writelines(lines)

# T02.01.00.00_04.99.51 
def incrementVersion(old_version):
    global log
    halves = old_version.split('_')
    parts = halves[1].split('.')
    increment_major_verison = None
    for i in range(len(parts),0,-1):
        if(increment_major_verison is None or increment_major_verison is True):
            step = int(parts[i-1]) + 1
        
        if(step > 99):
            parts[i-1] = '00'
            increment_major_verison = True
        else:
            parts[i-1] = f'{step:02}'
            increment_major_verison = False
            break
    return halves[0] + '_' + ".".join(parts)

def commitAndPushRepo(repo_path, message):
    global log
    try:
        repo_obj = git.Repo(repo_path)
        repo_obj.git.status()
        repo_obj.git.add(all=True)
        repo_obj.index.commit(message)
        origin = repo_obj.remote(name='origin')
        origin.push()
        log.info(f"""Pushed {getRepoName(repo_path)}""")
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")

def tagRepo(repo_path, message):
    global log
    try:
        repo_obj = git.Repo(repo_path)
        repo_obj.create_tag(message)
        origin = repo_obj.remote(name='origin')
        origin.push(message)
        log.info(f"""Tagged {getRepoName(repo_path)} with {message}""")
    except git.exc.GitError as e:
        log.info(f"""ERROR: {str(e)}""")

def renameArtefactsFolder(folder_path, new_name):
    global log
    parts = folder_path.split('/')
    parts[len(parts) - 1] = new_name
    new_path = "/".join(parts)
    os.rename(folder_path, new_path)
    log.info(f"""Renamed artefacts folder from {folder_path} to {new_path}""")
    return new_path
    
def zipdir(src, dst):
    global log
    os.chdir(os.path.dirname(src))
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            zf.write(absname, arcname)
    zf.close()
    log.info(f"""Zipped artefacts directory {abs_src+".zip"}""")
    return abs_src+".zip"

def copyFileToPath(src, dst):
    global log
    copyfile(src, dst)
    log.info(f"""Copied file {src} to {dst}""")

def updateValuesInManifest(xml_file, projects):
    global log
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    for dict in projects:
        #dict = project.attrib

        target_node = root.find(".//*[@name='"+dict['name']+"']")

        if('_version' in dict['name']):
            log.info('Setting ' + dict['name'] +' revision to : ' + dict['revision'])
            target_node.set('revision', dict['revision'])
        else:
            keys = dict.keys()
 
            target_node = root.find(".//*[@name='"+dict['name']+"']")
            if(target_node is None):
                log.info('Appending project ' + str(dict))
                target_node = root.makeelement('project', dict)
                root.append(target_node)

            for attr in keys:
                if(attr in ['revision', 'upstream']):
                    log.info('Setting ' + dict['name'] + ' ' + attr +
                        ' to : ' + dict[attr])
                    target_node.set(attr, dict[attr])

    tree.write(xml_file, encoding="UTF-8", xml_declaration=True)

def getValueFromManifest(xml_file, dict_predicate, attr_to_fetch):
    global log
    tree = ET.parse(xml_file)
    root = tree.getroot()
    predicate = ''
    keys = dict_predicate.keys()
    for attr in keys:
        predicate += "[@name='"+dict_predicate[attr]+"']"
    target_node = root.find(".//*"+predicate)
    if target_node is not None:
        return target_node.get(attr_to_fetch)
    return ''

    
def runBuildScript(script_path, script_args, build_log_path):
    global log
    log.info(f"""Running build script {script_path}""")
    with open(build_log_path, "w") as outfile:
        proc = subprocess.run([script_path, script_args], stdout=outfile)
        log.info(f"""Build script complete""")
        return proc.returncode
    

