from sys import version
import gitops

config = gitops.loadConfig('./config.yml')

version_repo = config['VERSION_REPO_BRANCH']
version_repo_path = config['PATH_REPO_SAVE_FOLDER']+config['VERSION_REPO_NAME']
version_repo_url = config['GIT_REMOTE_BASE_URL']+config['VERSION_REPO_NAME']
version_file_path = version_repo_path+'/version_build.h'
version_xml_path = version_repo_path+'/manifest.xml'

repositories = config['REPOSITORIES']

if gitops.repoCloned(version_repo_path) is False:
    gitops.cloneRepo(version_repo_url, config['VERSION_REPO_BRANCH'], version_repo_path)

build_necessary = False
for repo in repositories:
    repo_path = config['PATH_REPO_SAVE_FOLDER'] + repo['name']
    repo_url = config['GIT_REMOTE_BASE_URL'] + repo['name']
    if gitops.repoCloned(repo_path) is False:
        repo_obj = gitops.cloneRepo(repo_url, repo['branch'], repo_path)
    else:
        repo_obj = gitops.getRepoObj(repo_path)

    if gitops.remoteAhead(repo_obj, repo['branch']):
        build_necessary = True

version_num = gitops.getValueFromVersionFile(version_file_path, 'VERSION')
version_date = gitops.getValueFromVersionFile(version_file_path, 'DATE')

if(True): #build_necessary
    # gitops.updateValueInVerionFile(version_file_path, 'VERSION', version_num, 'NEWVERSION')
    # gitops.updateValueInVerionFile(version_file_path, 'DATE', version_num, 'NEWDATE')

    new_version_num = gitops.incrementVersion(version_num)
    print(new_version_num)

    gitops.updateValueInVerionFile(version_file_path, 'VERSION', version_num, new_version_num)
    gitops.commitAndPushRepo(version_repo_path, 'Success')