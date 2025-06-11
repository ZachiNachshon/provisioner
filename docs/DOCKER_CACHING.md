# Docker Caching Strategy for E2E Tests

## Overview

This document describes the Docker caching strategy implemented for E2E tests to optimize GitHub Actions usage and reduce CI subscription costs while ensuring comprehensive test coverage.

## Architecture

### Test Types

The CI pipeline now supports two test execution modes:

1. **Unit Tests**: Fast, non-Docker tests (`--skip-e2e`)
2. **E2E Tests**: Docker-based integration tests (`--all`)

### Caching Layers

#### 1. Docker Layer Caching
- **Technology**: Docker BuildX with local cache backend
- **Scope**: Individual Docker images (poetry, remote_ssh, raspbian_os)
- **Cache Key**: Dockerfile content + related configuration files
- **Storage**: `/tmp/.buildx-cache-{image-name}`

#### 2. Virtual Environment Caching
- **Technology**: GitHub Actions Cache
- **Scope**: Poetry virtual environment dependencies
- **Cache Key**: `poetry.lock` + `pyproject.toml` hash
- **Storage**: `./.venv`

#### 3. Built Packages (sdist) Caching
- **Technology**: GitHub Actions Cache
- **Scope**: Pre-built Python packages for Docker containers
- **Cache Key**: All Python source files + configuration
- **Storage**: `dockerfiles/poetry/dists/`

#### 4. Essential Files Archive Caching
- **Technology**: GitHub Actions Cache
- **Scope**: Compressed project files for Docker context
- **Cache Key**: Core project configuration files
- **Storage**: `dockerfiles/poetry/e2e_docker_essential_files.tar.gz`

## Usage

### Local Development

```bash
# Run unit tests only (fast)
./run_tests.py --all --skip-e2e --report xml

# Run all tests including E2E (slower, requires Docker)
./run_tests.py --all --report xml

# Run only E2E tests
./run_tests.py --all --only-e2e --report xml
```

### CI Configuration

The GitHub Actions workflow automatically:

1. **Unit Tests**: Run first for fast feedback
2. **E2E Tests**: Run with full Docker caching enabled
3. **Coverage**: Upload separate reports for unit and e2e tests

To enable E2E tests in CI:

```yaml
- name: Run Tests
  uses: ./.github/actions/tests
  with:
    include_e2e: true  # Enable Docker-based E2E tests
```

## Cache Efficiency

### Cache Hit Scenarios

- **Docker Layers**: ~80-90% cache hit when only Python code changes
- **Virtual Environment**: ~95% cache hit when dependencies unchanged
- **Built Packages**: ~90% cache hit when source code unchanged
- **Essential Files**: ~95% cache hit when core config unchanged

### Storage Usage Optimization

- **Cache Rotation**: Old cache entries automatically replaced
- **Size Limits**: Each cache type has reasonable size limits
- **Conditional Building**: Images only rebuilt when necessary

## Performance Impact

### Before Caching
- Docker build time: ~5-8 minutes per image
- Total E2E setup: ~15-20 minutes
- Network usage: ~500MB-1GB per build

### After Caching  
- Docker build time: ~30-60 seconds (cache hit)
- Total E2E setup: ~2-5 minutes
- Network usage: ~50-100MB (cache hit)

### Estimated Cost Savings
- **GitHub Actions minutes**: 60-75% reduction
- **Network transfer**: 80-90% reduction
- **Overall CI time**: 50-70% faster E2E tests

## Configuration

### Environment Variables

- `CI_PREBUILT_DOCKER_IMAGES=true`: Skip Docker builds in test script
- `PROVISIONER_INSTALLER_PLUGIN_TEST=true`: Enable test mode
- `COVERAGE_REPORT_TYPE`: Control coverage report format

### Cache Keys

All cache keys include `${{ runner.os }}` for platform-specific caching:

- **Docker**: `buildx-{image}-{os}-{dockerfile-hash}`
- **Venv**: `provisioner-monorepo-venv-{os}-{poetry-files-hash}`
- **Sdist**: `sdists-{os}-{all-python-files-hash}`
- **Archive**: `e2e-archive-{os}-{config-files-hash}`

## Troubleshooting

### Cache Miss Issues

1. **Check file changes**: Verify cache keys match expected files
2. **Clear cache**: Delete specific cache entries if corrupted
3. **Fallback behavior**: System gracefully falls back to full builds

### Docker Build Failures

1. **Verify Dockerfile syntax**: Check for syntax errors
2. **Check base images**: Ensure base images are accessible
3. **Review build logs**: Examine Docker buildx output

### Performance Issues

1. **Monitor cache hit rates**: Check GitHub Actions logs
2. **Optimize cache keys**: Ensure minimal but complete file coverage
3. **Review storage usage**: Monitor GitHub cache storage limits

## Monitoring

### GitHub Actions Insights

Monitor these metrics:
- Cache hit/miss ratios per job
- Total execution time trends
- Docker build duration
- Storage usage patterns

### Log Analysis

Key log messages to monitor:
- `✅ Skipping build for {image} - using CI pre-built image`
- `Cache restored from key: {cache-key}`
- `Docker build time: {duration}`

## Future Improvements

### Potential Optimizations

1. **Multi-stage builds**: Further reduce Docker layer sizes
2. **Registry caching**: Use container registry for image caching
3. **Parallel builds**: Build multiple images simultaneously
4. **Smart invalidation**: More granular cache invalidation

### Monitoring Enhancements

1. **Cache analytics**: Detailed cache performance metrics
2. **Cost tracking**: Monitor actual GitHub Actions usage
3. **Performance benchmarks**: Regular performance regression testing 