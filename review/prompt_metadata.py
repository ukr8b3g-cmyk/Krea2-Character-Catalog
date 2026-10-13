"""Resolve saved positive text without selecting unrelated/negative text nodes."""

SAMPLERS = {'KSampler', 'KSamplerAdvanced', 'SamplerCustom', 'SamplerCustomAdvanced'}
SAVERS = {'SaveImage', 'SaveWebPMeta', 'SaveImageWebP', 'SaveImageWithMetadata'}


def positive_prompt(api, snapshots):
    snapshots = snapshots if isinstance(snapshots, dict) else {}
    record = snapshots.get('record', snapshots)
    if isinstance(record, dict) and isinstance(record.get('generation_prompt'), str):
        return record['generation_prompt']
    if not isinstance(api, dict) or not api:
        values = {value['prompt'] for value in snapshots.values()
                  if isinstance(value, dict) and isinstance(value.get('prompt'), str)}
        if isinstance(snapshots.get('prompt'), str):
            values.add(snapshots['prompt'])
        return next(iter(values)) if len(values) == 1 else None

    nodes = {str(key): value for key, value in api.items() if isinstance(value, dict)}

    def link(value):
        if isinstance(value, list) and len(value) == 2 and isinstance(value[0], (str, int)) and isinstance(value[1], int):
            return str(value[0]), value[1]
        return None

    def common(values):
        return values[0] if values and all(value is not None and value == values[0] for value in values) else None

    def resolve(value, mode, seen=frozenset()):
        if mode == 'text' and isinstance(value, str):
            return value
        target = link(value)
        if not target or (target, mode) in seen or len(seen) > 100:
            return None
        node_id, slot = target
        node = nodes.get(node_id, {})
        kind, inputs = node.get('class_type'), node.get('inputs', {})
        if not isinstance(inputs, dict):
            return None
        seen = seen | {(target, mode)}
        follow = lambda item, next_mode=mode: resolve(inputs.get(item), next_mode, seen)
        if mode == 'text':
            if kind == 'Krea2CatalogPromptFile' and slot == 0:
                snapshot = snapshots.get(node_id, {})
                if isinstance(snapshot, dict) and isinstance(snapshot.get('prompt'), str):
                    return snapshot['prompt']
                text = inputs.get('manual_prompt')
                suffix = inputs.get('common_suffix', '')
                if isinstance(text, str) and text.strip() and isinstance(suffix, str):
                    return text.strip() + (', ' + suffix.strip() if suffix.strip() else '')
            return None
        if mode == 'conditioning':
            if kind == 'CLIPTextEncode' and slot == 0:
                return follow('text', 'text')
            if kind == 'TextEncodeQwenImage21' and slot == 0:
                return follow('prompt', 'text')
            if kind == 'ConditioningZeroOut':
                return ''
            if kind in {'ConditioningSetArea', 'ConditioningSetAreaPercentage', 'ConditioningSetTimestepRange'}:
                return follow('conditioning')
            if kind in {'ConditioningCombine', 'ConditioningConcat'}:
                return common([follow('conditioning_1'), follow('conditioning_2')])
            return None
        if kind in {'KSampler', 'KSamplerAdvanced', 'SamplerCustom'}:
            return follow('positive', 'conditioning')
        if kind == 'SamplerCustomAdvanced':
            return follow('guider', 'guider')
        if mode == 'guider':
            if kind == 'CFGGuider':
                return follow('positive', 'conditioning')
            if kind == 'BasicGuider':
                return follow('conditioning', 'conditioning')
            return None
        if kind in {'VAEDecode', 'VAEDecodeTiled', 'LatentUpscale', 'LatentUpscaleBy'}:
            return follow('samples', 'image')
        if kind in {'ImageScale', 'ImageScaleBy', 'ImageCrop'}:
            return follow('image', 'image')
        return None

    saves = [node for node in nodes.values() if node.get('class_type') in SAVERS]
    if saves:
        return common([resolve(node.get('inputs', {}).get('images'), 'image') for node in saves])
    # Without a save node, accept only an unambiguous sampler-positive result.
    return common([resolve([node_id, 0], 'image') for node_id, node in nodes.items()
                   if node.get('class_type') in SAMPLERS])
