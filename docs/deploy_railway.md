# Deploying on Railway

[Railway](https://railway.app) is a cloud hosting provider that is very simple to use.

## Prerequisites

- An account with Railway, whether on a free or paid plan.

## Basic Setup

The following instructions are for deploying `getgather` on your own Railway account. Many of the assumptions made here are for a basic setup with minimal web traffic, so you may want to tweak the settings to your liking.

#### 1. Install the Railway CLI

Follow the instructions for your local setup [here](https://docs.railway.com/guides/cli).

#### 2. Authenticate with Railway

Run the following command to log in to your Railway account:

```bash
railway login
```

#### 3. Initialize the Railway app

From the `getgather` repository, run:

```bash
railway init
```

The CLI will prompt you for a project name, which could be any of your choosing. In this example, we'll use `getgather` as the project name.

#### 4. Link the project

```bash
railway link
```

Simply select the project you just created.

#### 5. Create the service

A service is a subset of a project in Railway. You can name it whatever you want, but in this example, we'll just use `backend` as the service name.

```bash
railway add --service backend
```

You can set environment variables in step #6 here, or just hit enter to skip.

#### 6. Set Build Arguments

Set the following variable for your app.

```bash
railway variables --set PORT=23456 --service backend
```

You may also optionally consider setting other environment variables in the [Railway dashboard](https://railway.app/dashboard) or via the CLI. See also [`.env.template`](../.env.template) and the main [README](../README.md) for more information on environment variables.

#### 7. Deploy `getgather`

Run the following command to deploy `getgather` to Railway with the configuration that was set.

```bash
railway up
```

Railway will build and deploy the app, which will take a few minutes. At the end, when you see `INFO: Uvicorn running on http://0.0.0.0:23456 (Press CTRL+C to quit)`, you can press `CTRL+C` to exit, as this is just showing the logs.

#### 8. Create a domain

The following command will create a new domain for the app.

```bash
railway domain
```

The url to your app will be displayed from where you can access `getgather` directly. Test it out by opening the url in your browser.

#### 9. Access the app dashboard

If you run into any issues with accessing the running app, or want to view logs or other configuration options, run the following command to open the app dashboard in your browser.

```bash
railway open
```

Or, alternatively, you can access the app dashboard from the [Railway dashboard](https://railway.app/dashboard).

## Notes

In the Railway free-trial, you are limited to 1GB of RAM. It's possible you will need a paid plan to upgrade to a larger instance. `getgather` can run on 1 GB or RAM, but may be unstable, and 2 GB is recommended.
