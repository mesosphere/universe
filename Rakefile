REGISTRY = 'registry-agent.instana.io'
PKG_NAME = 'instana-agent'
IMAGE_NAME = 'mesosphere/universe-server'
TMP_DIR = "#{Dir.pwd}/tmp/.docker"

task default: [ :clear, :check, :deps, :build ]

desc 'Clear local workspace'
task :clear do
  sh %{ rm -rf #{TMP_DIR} && mkdir -p #{TMP_DIR} }

  images = `docker images`
  if images.include? IMAGE_NAME
    sh %{ docker rmi #{IMAGE_NAME}:instana-agent }
  end

  containers = `docker ps -a`
  if containers.include? "dind"
    sh %{ docker stop dind }
    sh %{ docker rm -f dind }
  end
end

desc 'Check JSON scheme'
task :check do
  raise 'Please set env vars DOCKER_READONLY_USER and DOCKER_READONLY_PW' if ENV['DOCKER_READONLY_USER'] == '' || ENV['DOCKER_READONLY_PW'] == ''
  sh %{ ./scripts/build.sh }
end

desc 'Package raw login bundle'
task :deps do
  sh %{ docker pull docker:dind }
  sh %{ docker run --privileged --name dind -d docker:dind }
  sleep 3
  sh %{ docker exec -ti -u root dind sh -c "docker login -u '#{ENV['DOCKER_READONLY_USER']}' -p '#{ENV['DOCKER_READONLY_PW']}' #{REGISTRY}" }
  sh %{ docker cp dind:/root/.docker/config.json #{TMP_DIR}/ }
  sh %{ docker stop dind && docker rm dind }
  sh %{ tar cfz docker.tar.gz tmp }
  sh %{ rm /tmp/docker.tar.gz } if File.exist?('/tmp/docker.tar.gz')
  sh %{ mv docker.tar.gz /tmp }
end

desc 'Build the package'
task :build do
  sh %{ DOCKER_TAG="#{PKG_NAME}" #{Dir.pwd}/docker/server/build.bash }
end