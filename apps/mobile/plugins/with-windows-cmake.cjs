const { withAppBuildGradle } = require('expo/config-plugins');

module.exports = function withWindowsCmake(config) {
  if (process.platform !== 'win32') return config;

  return withAppBuildGradle(config, (config) => {
    const gradle = config.modResults;
    if (gradle.contents.includes('CMAKE_OBJECT_PATH_MAX')) return config;

    const android = /^android \{$/m;
    const defaultConfig = /^( +)defaultConfig \{$/m;
    if (gradle.language !== 'groovy' || !android.test(gradle.contents) || !defaultConfig.test(gradle.contents)) {
      throw new Error('Expected a Groovy android block with defaultConfig in the generated app build file.');
    }

    // Let CMake hash deep React Native codegen object paths before Ninja builds them.
    gradle.contents = gradle.contents
      .replace(android, [
        'android {',
        '    externalNativeBuild {',
        '        cmake {',
        "            buildStagingDirectory file('../../../../build/cxx')",
        '        }',
        '    }',
      ].join('\n'))
      .replace(defaultConfig, (block, indent) => [
        block,
        `${indent}    externalNativeBuild {`,
        `${indent}        cmake {`,
        `${indent}            arguments "-DCMAKE_OBJECT_PATH_MAX=240"`,
        `${indent}        }`,
        `${indent}    }`,
      ].join('\n'));
    return config;
  });
};
