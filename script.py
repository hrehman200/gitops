import os
from sys import version
import gitops
from datetime import datetime

cfg = gitops.loadConfig('./cfg.yml')

gitops.setLogging(cfg['PATH_SCRIPT_LOG'])

version_repo = cfg['VERSION_REPO_BRANCH']
version_repo_path = cfg['PATH_REPO_SAVE_FOLDER']+cfg['VERSION_REPO_NAME']
version_repo_url = cfg['GIT_REMOTE_BASE_URL']+cfg['VERSION_REPO_NAME']
version_file_path = version_repo_path+'/version_build.h'
version_xml_path = version_repo_path+'/manifest.xml'

repositories = cfg['REPOSITORIES']
projects_xml = []

# clone version repo
if gitops.repoCloned(version_repo_path) is False:
    gitops.cloneRepo(version_repo_url, cfg['VERSION_REPO_BRANCH'], version_repo_path)

# pull version repo
if gitops.remoteAhead(version_repo_path, cfg['VERSION_REPO_BRANCH']):
    gitops.pullRepo(version_repo_path)

projects_xml.append({
    'name':cfg['VERSION_REPO_NAME'], 
    'revision':gitops.getRepoHash(version_repo_path)   
})

build_necessary = False

# clone or pull and decide whether build necessary
for repo in repositories:
    repo_path = cfg['PATH_REPO_SAVE_FOLDER'] + repo['name']
    repo_url = cfg['GIT_REMOTE_BASE_URL'] + repo['name']
    if gitops.repoCloned(repo_path) is False:
        gitops.cloneRepo(repo_url, repo['branch'], repo_path)
    elif gitops.remoteAhead(repo_path, repo['branch']):
        build_necessary = True

version_num = gitops.getValueFromVersionFile(version_file_path, 'VERSION')
version_date = gitops.getValueFromVersionFile(version_file_path, 'DATE')

new_version_num = gitops.incrementVersion(version_num)

if(build_necessary):

    for repo in repositories:
        repo_path = cfg['PATH_REPO_SAVE_FOLDER'] + repo['name']
        repo_url = cfg['GIT_REMOTE_BASE_URL'] + repo['name']
        gitops.pullRepo(repo_path)
        projects_xml.append({
            'name':repo['name'], 
            'revision':gitops.getRepoHash(repo_path),
            'upstream':gitops.getRepoHash(repo_path), #repo['branch']
        })

    return_code = gitops.runBuildScript(cfg['PATH_BUILD_SCRIPT'], cfg['PATH_BUILD_LOG'])
    build_successful = return_code == 0
    
    gitops.updateValuesInManifest(version_xml_path, projects_xml)
    
    # tag all repos
    if(build_successful):
        gitops.tagRepo(version_repo_path, cfg['TAG_PREFIX']+new_version_num)
        for repo in repositories:
            gitops.tagRepo(cfg['PATH_REPO_SAVE_FOLDER']+repo['name'], cfg['TAG_PREFIX']+new_version_num)

    # update version and date and push to version repo
    gitops.updateValueInVerionFile(version_file_path, 'VERSION', version_num, new_version_num)
    gitops.updateValueInVerionFile(version_file_path, 'DATE', version_date, datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
    gitops.commitAndPushRepo(version_repo_path, cfg['COMMIT_MESSAGE_PASS'])

    # rename, zip and move artefacts folder to network path
    artefact_build_dir = cfg['PATH_BUILD_ARTEFACTS_SOURCE']
    artefact_dir_new_name = cfg['ARTEFACTS_PREFIX']+'_'+new_version_num
    artefact_build_dir = gitops.renameArtefactsFolder(artefact_build_dir, artefact_dir_new_name)

    zipped_file_path = gitops.zipdir(artefact_build_dir, artefact_dir_new_name)
    zip_filename = os.path.basename(zipped_file_path)
    zip_file_on_network = cfg['PATH_BUILD_ARTEFACTS_DESTINATION']+zip_filename

    gitops.copyFileToPath(zipped_file_path, zip_file_on_network)

    # send email message
    email_message = f"""
        Build Result {zip_file_on_network}
        Build Manifest {version_xml_path}
        Build Log {cfg['PATH_BUILD_LOG']}
    """

    if(build_successful):
        email_subject = cfg['COMMIT_MESSAGE_PASS'] + ' ' + new_version_num
    else:
        email_subject = cfg['COMMIT_MESSAGE_FAIL'] + ' ' + new_version_num
    
    gitops.sendEmail(cfg['SEND_MAIL_DISTRIBUTION_LIST'], email_subject, email_message)

else:
    gitops.sendEmail(cfg['SEND_MAIL_DISTRIBUTION_LIST'], 'Build Results ' + new_version_num, 'No build necessary')