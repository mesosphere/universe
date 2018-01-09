# Tutorial for using the gen_universe script

The Universe repository provides tooling for generating your own Universe.

Clone the Universe repository with:
```bash
git clone git@github.com:mesosphere/universe
cd universe
```

Assuming that a package was created and saved in the following location:
```bash
tree ~/work/private-universe/
```
```bash
/home/user/work/private-universe/
├── packages
    └── H
        └── hello-world
            └── 0
                ├── config.json
                ├── marathon.json.mustache
                ├── package.json
                └── resource.json
```

Run the following script to generate the Universe JSON files:
```bash
scripts/gen_universe.py --repository ~/work/private-universe/packages/ --out-dir ~/work/private-universe/
```

This will result in the following files getting created. The files that end with `.json` are the content of Universe while files that end with `.content-type` are the content type of that Universe.
```bash
 tree ~/work/private-universe/
 /home/user/work/private-universe/
 ├── packages
 │   └── H
 │       └── hello-world
 │           └── 0
 │               ├── config.json
 │               ├── marathon.json.mustache
 │               ├── package.json
 │               └── resource.json
 ├── repo-empty-v3.content_type
 ├── repo-empty-v3.json
 ├── repo-up-to-1.10.content_type
 ├── repo-up-to-1.10.json
 ├── repo-up-to-1.11.content_type
 ├── repo-up-to-1.11.json
 ├── repo-up-to-1.6.1.zip
 ├── repo-up-to-1.7.zip
 ├── repo-up-to-1.8.content_type
 ├── repo-up-to-1.8.json
 ├── repo-up-to-1.9.content_type
 ├── repo-up-to-1.9.json
 ├── universe.content_type
 └── universe.json
```

Upload the generated files to an HTTP server. If you are using S3 you can:
```bash
aws s3 cp --content-type "$(cat ~/work/private-universe/repo-up-to-1.10.content-type)" ~/work/private-universe/repo-up-to-1.10.json s3://host/and/path/to/repo-up-to-1.10.json
```

After uploading those files to an HTTP server (S3 for example), configure DC/OS (Cosmos) to use that repository:

```bash
dcos package repo add --index=0 "Private Universe" https://host/and/path/to/repo-up-to-x.json
```

Finally, you can start a service from that DC/OS Package with:
```bash
dcos package install hello-world
```
