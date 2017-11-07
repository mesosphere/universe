
During major/minor updates, some test branches can go out of date and this may result in breaking some integration tests. In order to resolve this, we need to make sure that the test branches have the same source code as the default branch. At the time of this writing, some of the test branches in use are : 

* `cli-test-v3-helloworld`
* `cli-test-4`


# Steps to update branch

1. Checkout the default branch of universe (`version-3.x` at the time of this writing).
2. Checkout the non default branch you want to update. E.g.: `cli-test-v3-helloworld` in to a different directory. 
3. Copy all the contents of the repo from the default branch to non-default branch. (Copy with overwrite)
4. By doing this, you are essentially updating the `code` part of the repo such as config, code, and readme files.
5. Create a branch with your new changes (Some files may be deleted, some updated - don't worry). Make sure you don't have any changes in the `repo/packages` directory. 
6. Create a PR to trigger the universe CI's and for the docker image, you can refer to [this teamcity build](https://teamcity.mesosphere.io/viewType.html?buildTypeId=Oss_Universe_UniverseServer).