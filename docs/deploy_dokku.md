# Deploying on Dokku

[Dokku](https://dokku.com/) is a lightweight PaaS that runs on top of Docker. It can be used to deploy a web app or an API.

To setup the instance, follow these instructions, but your instance may be different based on your needs.

## Instructions

### Create a GCE Instance

Much of these instructions may be able to be adapted to other cloud providers.

_From Google Cloud console:_

#### 1. Create a new instance of [Compute Engine](https://cloud.google.com/compute/docs/). Choose Debian 12 as the OS. Make sure to _Allow HTTP Traffic_ and _Allow HTTPS Traffic_ in the _Firewall_ config.

#### 2. From the VPC configuration, reserve a new public (external) IPv4 address and assign it to the instance. This is to ensure that the instance does not only have an ephemeral IP address.

#### 3. If you have a domain for your application, now would be a good time to set up an A record to point to the IP address of the instance too.

### Setup Dokku

There are several ways to SSH into the VM. All of which are acceptable

- Browser-based SSH: Clicking "SSH" button in the GCE Console _(easiest)_
- SSHing directly from the command line: `ssh USER@IPADDRESS`
- Using a `gcloud` command: `gcloud compute ssh --zone "MY_ZONE" "VM_NAME" --project "PROJECT_NAME"`

_From the remote login/ssh session, run the following commands:_

#### 4. Ensure [unattended upgrades](https://wiki.debian.org/UnattendedUpgrades) for automatic security patches with:

```bash
sudo apt update && sudo apt upgrade
sudo apt install unattended-upgrades
```

#### 5. Install [Nginx](https://nginx.org/) and then check that the web server is running and accessible from the outside world (note the external IPv4 address of the said instance):

```bash
sudo apt install nginx
```

#### 6. Install Dokku by following its [installation documentation](https://dokku.com/docs/getting-started/installation/).

```bash
# for debian systems, installs Dokku via apt-get
wget -NP . https://dokku.com/install/v0.35.20/bootstrap.sh
sudo DOKKU_TAG=v0.35.20 bash bootstrap.sh
```

#### 7. [Add a new SSH key](https://dokku.com/docs/deployment/user-management/#adding-ssh-keys) to allow remote access and deployment to Dokku.

This makes it easy to deploy from a local machine later.

```bash
echo "$YOUR_SSH_PUBLIC_KEY" | sudo dokku ssh-key:add github@getgather.com
```

#### 8. Install Dokku's Let's Encrypt plugin (necessary for automatic SSL certificate):

```bash
sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
```

### Configure the Application

The following commands can be run from a local machine using the alias `dokku` (see below), or they may be run on the remote machine directly via SSH/login.

_Create a helpful alias for the remote machine:_

```bash
alias dokku="ssh dokku@IPADDRESS"
```

#### 9. Make sure that Dokku on the remote instance is accessible, e.g. by checking its version:

```bash
dokku version
```

#### 10. Create a new app called `getgather` and configure some basic settings:

```bash
dokku apps:create getgather
dokku ports:add getgather http:80:8000
dokku ports:add getgather https:443:8000
dokku domains:set getgather <YOUR_DOMAIN>
dokku nginx:set getgather proxy-read-timeout 600s
dokku nginx:set getgather proxy-connect-timeout 600s
dokku nginx:set getgather proxy-send-timeout 600s
dokku nginx:set getgather send-timeout 600s
dokku proxy:build-config getgather
```

#### 11. Attempt a manual deployment first. From a git checkout of Get Gather repository (from a local machine outside of the VM):

```bash
git remote add dokku dokku@<VM_IP_ADDRESS>:getgather
git push dokku main
```

#### 12. Enable automatic SSL/TLS certificate:

```bash
dokku letsencrypt:set getgather email <YOUR_EMAIL>
dokku letsencrypt:enable getgather
dokku letsencrypt:cron-job --add
```

#### 13. To facilitate [zero-downtime deployment](https://dokku.com/docs/deployment/zero-downtime-deploys/), adjust the grace period for Docker stop:

```bash
dokku config:set getgather DOKKU_DOCKER_STOP_TIMEOUT=30
```

#### 14. If there is insufficient disk space, it can lead to deployment failures. To fix this, [remove unused Docker images and other related stuff](https://docs.docker.com/config/pruning/#prune-everything) with:

```bash
sudo docker system prune -f -a --volumes
```

#### 15. Set up a cronjob to perform the pruning. First open the crontab file:

```bash
sudo crontab -e
```

Add the following line, which does the pruning every hour:

```bash
3 * * * * docker system prune -f -a --volumes
```

## Continuous Deployment via GitHub Actions

Deployment is triggered automatically via git push, which runs the [deploy workflow](./github/workflows/deploy-dokku.yml). This workflow needs 3 [repository secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-a-repository):

- `DOKKU_SSH_PRIVATE_KEY`
- `DOKKU_SSH_HOST_KEY`
- `DOKKU_GIT_REMOTE_URL`

First, create a new SSH key (mark it as e.g. `github@getgather.com`). Add the public key to Dokku, following [its documentation](https://dokku.com/docs/deployment/user-management/#adding-ssh-keys). Copy the private key and use it for `DOKKU_SSH_PRIVATE_KEY`.

Meanwhile, `DOKKU_SSH_HOST_KEY` is obtained by scanning the instance:

```bash
ssh-keyscan -t rsa <VM_IP_ADDRESS>
```

Be sure to copy the whole thing (starting with `#`)

Last but not least, `DOKKU_GIT_REMOTE_URL` is in the form of `dokku@<VM_IP_ADDRESS>:getgather` (see the alias in Step 8).
