from diagrams import Cluster, Diagram, Edge
from diagrams.custom import Custom
from diagrams.programming.language import Python

BAZEL_ICON_PATH = "rpi/os/diagrams/bazel.png"
BUILDKITE_ICON_PATH = "rpi/os/diagrams/buildkite.png"
NPM_PACKAGE_ICON_PATH = "rpi/os/diagrams/npm_package.png"
NPM_REGISTRY_ICON_PATH = "rpi/os/diagrams/npm_registry.png"
BUILDBUDDY_PACKAGE_ICON_PATH = "rpi/os/diagrams/buildbuddy.png"
WIX_MUSA_ICON_PATH = "rpi/os/diagrams/wix-musa.png"
JFROG_ARTIFACTORY_ICON_PATH = "rpi/os/diagrams/jfrog_artifactory.png"
JSON_ICON_PATH = "rpi/os/diagrams/json.png"
TAR_ICON_PATH = "rpi/os/diagrams/tar.png"


def main():
    with Diagram("NPM Proto Sync", show=False):

        with Cluster("Build"):
            bazel = Custom(label="Bazel", icon_path=BAZEL_ICON_PATH)
            with Cluster("Packaging"):
                tar_archive = Custom(label="proto-sources.tar.gz", icon_path=TAR_ICON_PATH)
                package_json = Custom(label="package.json", icon_path=JSON_ICON_PATH)
                wix_npm_proto_package_rule = Python(label="wix_npm_proto_package")
                wix_npm_proto_package_rule >> [tar_archive, package_json]

        with Cluster("Version Stamping"):
            artifactory = Custom(label="Artifactory", icon_path=JFROG_ARTIFACTORY_ICON_PATH)
            async_publisher = Custom(label="Async Publisher", icon_path=WIX_MUSA_ICON_PATH)
            npm_package = Custom(label="NPM Package", icon_path=NPM_PACKAGE_ICON_PATH)
            async_publisher << Edge(label="read version") << artifactory
            async_publisher >> Edge(label="write next version") >> artifactory

        buildbuddy = Custom(label="BuildBuddy Result Store", icon_path=BUILDBUDDY_PACKAGE_ICON_PATH)

        bazel >> wix_npm_proto_package_rule

        npm_registry = Custom(label="NPM Registry", icon_path=NPM_REGISTRY_ICON_PATH)
        [tar_archive, package_json] >> Edge(label="write") >> buildbuddy << Edge(label="read") << async_publisher

        async_publisher >> Edge(label="next version stamp") >> npm_package >> npm_registry

        buildkite = Custom(label="Buildkite", icon_path=BUILDKITE_ICON_PATH)
        buildkite >> bazel


if __name__ == "__main__":
    main()
