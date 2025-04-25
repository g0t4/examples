## first captures on start zed:

```json
{
    "outline": "```untitled\n```\n",
    "input_events": "",
    "input_excerpt": "```untitled\n<|start_of_file|>\n<|editable_region_start|>\n\n\n\n<|user_cursor_is_here|>\n<|editable_region_end|>\n```",
    "speculated_output": "<|editable_region_start|>\n\n\n\n<|user_cursor_is_here|>\n<|editable_region_end|>",
    "can_collect_data": false,
    "diagnostic_groups": null   #
}
{
    "outline": "```untitled\n```\n",
    "input_events": "",
    "input_excerpt": "```untitled\n<|start_of_file|>\n<|editable_region_start|>\n\n\n\n<|user_cursor_is_here|>\n<|editable_region_end|>\n```",
    "speculated_output": "<|editable_region_start|>\n\n\n\n<|user_cursor_is_here|>\n<|editable_region_end|>",
    "can_collect_data": false,
    "diagnostic_groups": null
}
```

## request after I made a change and typed "set"

```json
{
     "outline": "```fish/load_last/misc-specific.fish\nfunction on_change_show_verbose_prompt\nfunction toggle_show_verbose_prompt\nfunction _k3s_autocomplete\nfunction kgdump\nfunction _abbr_kgv\nfunction kdd\nfunction kns\nfunction
 dig\nfunction helm_template_diff\nfunction pstreeX\nfunction pstree\nfunction _flush_dns\nfunction kill_hung_grc\nfunction z\nfunction custom-kill-command-word\nfunction toggle-grc\nfunction dpkg_L_files\nfunction dpkg_L_tree\nfunction
 treeify\nfunction dpkg_tree_awk\nfunction watch\nfunction wordcount\nfunction yq_diff_docs\nfunction tellme_about\nfunction _indent\nfunction actw_expanded\nfunction ols_qwen_debug\nfunction ols_qwen\nfunction cd2\nfunction
 elgato_diff_ProfilesV2\nfunction elgato_sync_ProfilesV2_dry_run\nfunction elgato_sync_ProfilesV2\nfunction elgato_kill_other_account_streamdeck\nfunction _path_list\nfunction quote_paths\nfunction video_editing_total_duration\nfunction
 abbr_check\nfunction abbr_videos_glob_for_current_dir\nfunction video_editing_1_check_audio\nfunction abbr_30fps\nfunction video_editing_2_convert_30fps\nfunction video_editing_extract_most_scene_change_thumbnails\nfunction
 abbr_mp4\nfunction _video_editing_ffmpeg_file_list\nfunction _get_first_file_extension\nfunction _get_first_file_dir\nfunction _get_output_file_based_on_first_file\nfunction _ffmpeg_concat\nfunction abbr_aio\nfunction
 video_editing_just_shift_to_mp4_one_video\nfunction video_editing_aio\nfunction video_editing_gen_fcpxml\nfunction abbr_db\nfunction video_editing_boost_audio_dB_by\nfunction bitmaths\nfunction pretty_size\nfunction
 show_hex_rgb_color\nfunction _screenshots_trash_secondary_display\nfunction move_screenshots_from_last_x_hours\nfunction find_huge_files\nfunction __pmtreeX\nfunction zedraw\nfunction zedfull\nfunction trash\nfunction abbr_agg\nfunction
 _taild\n```\n",
     "input_events": "User edited \"fish/load_last/misc-specific.fish\":\n```diff\n@@ -20,7 +20,6 @@\n     if not set --query show_verbose_prompt\n         set --universal show_verbose_prompt yes\n     else\n-        set \n         set
 --universal --erase show_verbose_prompt\n     end\n     # commandline --function repaint\n\n```",
     "input_excerpt": "```dotfiles/fish/load_last/misc-specific.fish\n### FISH HELP ###\nset __fish_help_dir \"\" # overwrite fish help dir thus forcing the use of https://fishshell.com instead of local files (which I prefer b/c I have
 highlighting of fishshell.com pages) # ... try it with: `help help` => opens https://fishshell.com/docs/3.6/interactive.html#help\n# see `type help` to find the part of the help command that decides what to
 open\n<|editable_region_start|>\n\n### BINDINGS ###\n# some of these might be a result of setting up iTerm2 to use xterm default keymapping (in profile), might need to adjust if key map is subsequently changed\n# bind shift-delete kill-word
 # shift+del to kill forward a word (otherwise its esc+d only), I have a habit of using this (not sure why, probably an old keymapping in zsh or?)\n#  dont wanna clobber new shift-delete in autosuggests... and I don't think I used
 shift-delete often for delete forward anyways\nfunction on_change_show_verbose_prompt --on-variable show_verbose_prompt\n    commandline --function repaint\nend\nfunction toggle_show_verbose_prompt\n    if not set --query
 show_verbose_prompt\n        set --universal show_verbose_prompt yes\n    else\n        set<|user_cursor_is_here|> --universal --erase show_verbose_prompt\n    end\n    # commandline --function repaint\nend\nbind f4
 toggle_show_verbose_prompt\n\nif command -q launchctl\n    abbr lcl 'launchctl list'\n    abbr lcp 'launchctl print system'\n    abbr lcpu 'launchctl print user/$(id -u)'\n    abbr lcpg 'launchctl print gui/$(id -u)'\n    abbr lcds
 'launchctl disable system/'\n<|editable_region_end|>\n    abbr lcdu 'launchctl disable user/$(id -u)'\n    abbr lcdg 'launchctl disable gui/$(id -u)'\n```",
     "speculated_output": "<|editable_region_start|>\n\n### BINDINGS ###\n# some of these might be a result of setting up iTerm2 to use xterm default keymapping (in profile), might need to adjust if key map is subsequently changed\n# bind
 shift-delete kill-word # shift+del to kill forward a word (otherwise its esc+d only), I have a habit of using this (not sure why, probably an old keymapping in zsh or?)\n#  dont wanna clobber new shift-delete in autosuggests... and I don't
 think I used shift-delete often for delete forward anyways\nfunction on_change_show_verbose_prompt --on-variable show_verbose_prompt\n    commandline --function repaint\nend\nfunction toggle_show_verbose_prompt\n    if not set --query
 show_verbose_prompt\n        set --universal show_verbose_prompt yes\n    else\n        set<|user_cursor_is_here|> --universal --erase show_verbose_prompt\n    end\n    # commandline --function repaint\nend\nbind f4
 toggle_show_verbose_prompt\n\nif command -q launchctl\n    abbr lcl 'launchctl list'\n    abbr lcp 'launchctl print system'\n    abbr lcpu 'launchctl print user/$(id -u)'\n    abbr lcpg 'launchctl print gui/$(id -u)'\n    abbr lcds
 'launchctl disable system/'\n<|editable_region_end|>",
     "can_collect_data": false,
     "diagnostic_groups": []
} 
```



## vllm response example (python rich print)

```json

// vllm prompt log:
'### Instruction:\nYou are a code completion assistant and your task is to analyze user edits and then rewrite an excerpt that the user provides, suggesting the appropriate edits within the excerpt, taking into account the cursor location.\n\n### User Edits:\n\nUser edited "lua/ask-openai/prediction/tests/calc/calc.lua":\n```diff\n@@ -7,4 +7,5 @@\n \n \n \n+\n return M\n\n```\n\nUser edited "lua/ask-openai/prediction/tests/calc/calc.lua":\n```diff\n@@ -8,4 +8,5 @@\n \n \n \n+\n return M\n\n```\n\n### User Excerpt:\n\n```ask-openai.nvim/lua/ask-openai/prediction/tests/calc/calc.lua\n<|start_of_file|>\n<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n<|user_cursor_is_here|>\n\n\n\n\n\nreturn M\n\n<|editable_region_end|>\n```\n\n### Response:\n'

// vllm response:
{
    'id': 'cmpl-1e2dd241cbba4f2e8b8ccfa26af7636b',
    'object': 'text_completion',
    'created': 1745566545,
    'model': 'zed-industries/zeta',
    'choices': [
        {
            'index': 0,
            'text': '<|editable_region_start|>\nlocal M = {}\n\nfunction M.add(a, b)\n    return a + b\nend\n\nfunction
M.subtract(a, b)\n    return a - b\nend\n\nfunction M.multiply(a, b)\n    return a * b\nend\n\nfunction M.divide(a,
b)\n    if b == 0 then\n        error("Division by zero")\n    end\n    return a / b\nend\n\nreturn
M\n\n<|editable_region_end|>\n```\n',
            'logprobs': None,
            'finish_reason': 'stop',
            'stop_reason': None,
            'prompt_logprobs': None
        }
    ],
    'usage': {'prompt_tokens': 209, 'total_tokens': 311, 'completion_tokens': 102, 'prompt_tokens_details': None}
}
```
