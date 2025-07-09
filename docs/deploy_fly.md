# Deploying on Fly.io

[Fly.io](https://fly.io) is a paid cloud hosting provider that automatically scales your app based on traffic. It's very simple to configure and deploy to.

## Prerequisites

- An account with Fly.io, whether on a free or paid plan.

## Basic Setup

The following instructions are for deploying `getgather` on your own Fly.io account. Many of the assumptions made here are for a basic setup with minimal web traffic, so you may want to tweak the settings to your liking.

#### 1. Install the Fly CLI

Follow the instructions for your local setup [here](https://fly.io/docs/flyctl/install/).

#### 2. Log in to Fly.io:

Run the following command to log in to your Fly.io account:

```bash
fly auth login
```

#### 3. Initialize the app

From the `getgather` repository, run:

```bash
fly launch
```

#### 4. Configure the app

You will be prompted to tweak the settings before proceeding. Enter `yes` to proceed to the web UI for the settings. Otherwise, you will be able to configure the settings later via the UI or the `fly.toml` file.

```bash
? Do you want to tweak these settings before proceeding? (y/n): y
```

#### 5. Enter the following settings for basic usage. You may want to tweak these settings later.

- App Name: (Pick a unique name for your app, such as `getgather`)
- Region: (Pick a region closest to you, or that Fly.io recommends)
- Internal Port: `8000` (You can change this to any port you want, but 8000 is the default for the application)
- Machine Size: `shared-cpu-2x` (or a larger size if you need more resources)
- Memory: `2GB` (or a larger amount if you need more memory)

All other settings can be left as default or turned off.

#### 6. Confirm the settings.

Your running terminal will proceed to build and deploy the app using the Dockerfile to Fly.io, and also generate a `fly.toml` file in the root directory of the repository. This file contains the configuration for your Fly.io app, and can be adjusted to your liking. It may also automatically create a `fly-deploy.yml` file in the `.github/workflows` directory of the repository. This file contains the configuration for automatic deployment from GitHub Actions, and can be ignored/deleted if you don't want to use GitHub Actions.

#### 7. Set Environment Variables and Build Arguments

You should consider adding any build arguments and environment variables (see also [`.env.template`](../.env.template) and [``](build args)) to the `[env]` section of the `fly.toml` file. For more information on what each variable is used for, please see the main [README](../README.md).

```toml
[build.args]
  BUILD_ARG=value

[env]
    ENV_VAR=value
```

#### 8. Set secrets

If you don't want to expose any of these environment variables in your `fly.toml` file, you can set secrets instead by running this command:

```bash
fly secrets set ENV_VAR="value"
```

#### 9. Re-deploy the app to apply the changes

Running the following command will re-deploy the app to apply the environment variables and other changes you made.

```bash
fly deploy
```

#### 10. Access your app

You can now access your app at `https://<your-app-name>.fly.dev` (or whatever the domain is that Fly.io assigns to your app).
