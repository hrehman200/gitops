import yaml
import git
import os
import zipfile
from shutil import copyfile
import smtplib
from email.message import EmailMessage
import xml.etree.ElementTree as ET
import logging
import subprocess

log = object

def loadConfig(configPath):
    with open('config.yml') as c:
        config = yaml.load(c, yaml.SafeLoader)
        return config

def setLogging(log_file_path):
    logging.basicConfig(format='[%(asctime)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO,
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ])
    log = logging.getlog(__name__)
    log.info('Setting logging')

def repoCloned(path):
    cloned = os.path.isdir(path)
    log.info(f"""Repo {path }exists : {cloned}""")
    return cloned

def cloneRepo(url, branch, folder):
    log.info(f"""Cloning repo {url} {branch} to dir {folder} """)
    return git.Repo.clone_from(url, folder, branch=branch)

def pullRepo(repo_path):
    log.info(f"""Pulling repo {getRepoName(repo_path)} """)
    repo = git.Repo(repo_path)
    o = repo.remotes.origin
    o.pull()

def getRepoHash(repo_path):
    repo = git.Repo(repo_path)
    sha = repo.head.object.hexsha
    return sha

def getRepoObj(folder):
    return git.Repo(folder)

def getRepoName(repo_path):
    repo = git.Repo(repo_path)
    return repo.remotes.origin.url.split('.git')[0].split('/')[-1]

def remoteAhead(repo_path, branch):
    repo_obj = git.Repo(repo_path)
    commits_diff = repo_obj.git.rev_list('--left-right', '--count', f'{branch}...{branch}@{{u}}')
    num_ahead, num_behind = commits_diff.split('\t')
    ahead = int(num_ahead) > 0
    log.info(f"""Repo {getRepoName(repo_path)} is ahead? : {ahead}""")
    return ahead

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
                log.info(f"""Updating {key} to : {newValue}""")
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
    repo_obj = git.Repo(repo_path)
    repo_obj.index.commit(message)
    origin = repo_obj.remote(name='origin')
    origin.push()
    log.info(f"""Pushed {getRepoName(repo_path)}""")

def tagRepo(repo_path, message):
    repo_obj = git.Repo(repo_path)
    repo_obj.create_tag(message)
    origin = repo_obj.remote(name='origin')
    origin.push(message)
    log.info(f"""Tagged {getRepoName(repo_path)} with {message}""")

def renameArtefactsFolder(folder_path, new_name):
    parts = folder_path.split('/')
    parts[len(parts) - 1] = new_name
    new_path = "/".join(parts)
    os.rename(folder_path, new_path)
    log.info(f"""Renamed artefacts folder from {folder_path} to {new_path}""")
    return new_path
    
def zipdir(src, dst):
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
    copyfile(src, dst)

def sendEmail(to, subject, message):
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = subject
    msg['From'] = 'sender@gmail.com'
    msg['To'] = to

    with smtplib.SMTP("mail.siemens.de") as server:
        #server.login(user, password)
        server.send_message(msg)
        log.info(f"""Sent email with subject {subject} to {to}""")

def updateValuesInManifest(xml_file, projects):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    for dict in projects:
        #dict = project.attrib

        target_node = root.find(".//*[@name='"+dict['name']+"']")

        if('_version' in dict['name']):
            log.ino('Setting ' + dict['name'] +' revision to : ' + dict['revision'])
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

                    log.info('Setting ' + dict['name'] +
                        ' upstream to : ' + dict['revision'])
                    target_node.set('upstream', dict['revision'])

    tree.write(xml_file, encoding="UTF-8", xml_declaration=True)
    
def runBuildScript(script_path):
    log.info(f"""Running build script {script_path}""")
    output = subprocess.Popen(script_path, shell=True, stdout=subprocess.PIPE).stdout.read()
    log.info(f"""Build script complete: {output}""")
    return output

