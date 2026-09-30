import json

from django.core.exceptions import ValidationError
from core.models import HomeDynamicSection, ImageAsset
from django.core.validators import URLValidator

BUTTON_FIELDS = ('button_label', 'button_url', 'secondary_label', 'secondary_url')


def validate_button_url(value):
    if not value:
        return
    if any(char.isspace() or char == '\\' for char in value):
        raise ValidationError('Endereço de botão inválido.')
    if value.startswith('/') and not value.startswith('//'):
        return
    URLValidator(schemes=['http', 'https'])(value)


def parse_components(raw, user=None):
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        raise ValidationError('Configuração de componentes inválida.')
    if not isinstance(data, list) or len(data) > 50:
        raise ValidationError('Use no máximo 50 componentes.')
    result = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValidationError('Componente inválido.')
        for key in ('title', 'content', 'kind', 'eyebrow', 'image_url') + BUTTON_FIELDS:
            if not isinstance(item.get(key, ''), str):
                raise ValidationError('Os campos do componente devem ser textos.')
        if not isinstance(item.get('is_visible'), bool):
            raise ValidationError('Visibilidade inválida.')
        section = HomeDynamicSection(
            title=item.get('title', '').strip(), content=item.get('content', '').strip(),
            kind=item.get('kind', 'text'), eyebrow=item.get('eyebrow', '').strip(),
            image_url=item.get('image_url', '').strip(), is_visible=item['is_visible'],
            display_order=index + 1,
        )
        asset_id = item.get('image_asset_id')
        for key in BUTTON_FIELDS:
            setattr(section, key, item.get(key, '').strip())
        for label, link in [('button_label', 'button_url'), ('secondary_label', 'secondary_url')]:
            validate_button_url(getattr(section, link))
            if bool(getattr(section, label)) != bool(getattr(section, link)):
                raise ValidationError('Preencha o texto e o endereço do botão, ou deixe ambos vazios.')
        if asset_id:
            if not user or not isinstance(asset_id, int):
                raise ValidationError('Imagem inválida.')
            asset = ImageAsset.objects.filter(pk=asset_id).first()
            if not asset or (asset.owner_id != user.pk and not HomeDynamicSection.objects.filter(image_asset=asset).exists()):
                raise ValidationError('Imagem não disponível.')
            section.image_asset = asset
        section.full_clean(exclude=['content'], validate_unique=False, validate_constraints=False)
        if len(section.content) > 20000:
            raise ValidationError('O texto deve ter no máximo 20.000 caracteres.')
        result.append(section)
    return result


def serialize_components():
    result = []
    for section in HomeDynamicSection.objects.select_related('image_asset'):
        item = {key: getattr(section, key) for key in ('title', 'content', 'kind', 'eyebrow', 'image_url', 'is_visible', 'image_asset_id') + BUTTON_FIELDS}
        if section.image_asset:
            asset = section.image_asset
            item['image_asset_info'] = {key: getattr(asset, key) for key in ('source', 'x', 'y', 'zoom', 'ratio')}
        result.append(item)
    return result
