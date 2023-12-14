# Game Settings

The game setting is specified in the `default_settings.yaml` file under the civrealm folder. To overwrite a setting, you can do either of the following:

- Directly change the value in the `default_settings.yaml` file. Or
- Use the `--setting` argument. For example, to set the maximum number of turns to 5 for a quick test, you can use the following command:

```bash
test_civrealm --max_turns 5
```

The details of the game setting are as follows:

## Basic Settings for Game Play

{{ read_csv('game_setting_tables/basic_settings.csv', keep_default_na=False) }}

## Settings for parallel running

{{ read_csv('game_setting_tables/parallel.csv', keep_default_na=False) }}

## Settings for debug

{{ read_csv('game_setting_tables/debug.csv', keep_default_na=False) }}
