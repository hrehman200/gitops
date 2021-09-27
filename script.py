import os
from sys import version
import gitops
from datetime import datetime
import emailer

cfg = gitops.loadConfig('./cfg.yml')

log = gitops.setLogging(cfg['PATH_SCRIPT_LOG'])

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

# pull version repo, if commit hashes differ
if gitops.getRepoHash(version_repo_path) != gitops.getValueFromManifest(version_xml_path, {'name':cfg['VERSION_REPO_NAME']}, 'revision'):
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
        build_necessary = True
    elif gitops.getRepoHash(repo_path) != gitops.getValueFromManifest(version_xml_path, {'name':repo['name']}, 'revision'):
        build_necessary = True

version_num = gitops.getValueFromVersionFile(version_file_path, 'VERSION')
version_date = gitops.getValueFromVersionFile(version_file_path, 'DATE')

if(build_necessary):

    new_version_num = gitops.incrementVersion(version_num)
    log.info(f"""Building Version:: {new_version_num} :: from branch {version_repo}""")

    # log version to build log 
    f = open(cfg['PATH_BUILD_LOG'], "a")
    f.write(f"""Building Version:: {new_version_num} :: from branch {version_repo}""")
    f.close()

    for repo in repositories:
        repo_path = cfg['PATH_REPO_SAVE_FOLDER'] + repo['name']
        repo_url = cfg['GIT_REMOTE_BASE_URL'] + repo['name']
        gitops.pullRepo(repo_path)
        projects_xml.append({
            'name':repo['name'], 
            'revision':gitops.getRepoHash(repo_path),
            'upstream':repo['branch']
        })

    return_code = gitops.runBuildScript(cfg['PATH_BUILD_SCRIPT'], cfg['ARGUMENTS_BUILD_SCRIPT'], cfg['PATH_BUILD_LOG'])
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
    gitops.commitAndPushRepo(version_repo_path, cfg['COMMIT_MESSAGE_PASS'] if build_successful else cfg['COMMIT_MESSAGE_FAIL'])

    # copy log files to artefacts folder
    script_log_filename = os.path.basename(cfg['PATH_SCRIPT_LOG'])
    build_log_filename = os.path.basename(cfg['PATH_BUILD_LOG'])
    gitops.copyfile(cfg['PATH_SCRIPT_LOG'], f"""{cfg['PATH_BUILD_ARTEFACTS_SOURCE']}/{script_log_filename}_{new_version_num}_{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}""")
    gitops.copyfile(cfg['PATH_SCRIPT_LOG'], f"""{cfg['PATH_BUILD_ARTEFACTS_SOURCE']}/{build_log_filename}_{new_version_num}_{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}""")

    # rename, zip and move artefacts folder to network path
    artefact_build_dir = cfg['PATH_BUILD_ARTEFACTS_SOURCE']
    artefact_dir_new_name = cfg['ARTEFACTS_PREFIX']+'_'+new_version_num
    artefact_build_dir = gitops.renameArtefactsFolder(artefact_build_dir, artefact_dir_new_name)

    zipped_file_path = gitops.zipdir(artefact_build_dir, artefact_dir_new_name)
    zip_filename = os.path.basename(zipped_file_path)
    zip_file_on_network = cfg['PATH_BUILD_ARTEFACTS_DESTINATION']+zip_filename

    gitops.copyFileToPath(zipped_file_path, zip_file_on_network)

    if(build_successful):
        emailer.sendBuildSuccessEmail(cfg, zip_file_on_network, version_xml_path, new_version_num, log)
    else:
        emailer.sendBuildFailEmail(cfg, zip_file_on_network, version_xml_path, new_version_num, log)

    # rename build files
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    os.rename(cfg['PATH_BUILD_LOG'], f"""{cfg['PATH_BUILD_LOG']}_{new_version_num}_{timestamp}""")
    os.rename(cfg['PATH_SCRIPT_LOG'], f"""{cfg['PATH_SCRIPT_LOG']}_{new_version_num}_{timestamp}""")

else:
    log.info(f"""No build necessary""")
    emailer.sendNoBuildNeededEmail(cfg, log)