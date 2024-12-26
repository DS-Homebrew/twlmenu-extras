#!/bin/bash

# Add new languages here, space separated and using the ID for `crowdin pull`
LANGUAGES="da de es-ES fr he hu in-context id it ja ko nl no pl pt-PT pt-BR ro ru sv-SE tr uk zh-CN"

ARG=''
for LANGUAGE in $LANGUAGES; do
	ARG+="-l $LANGUAGE "
done
crowdin pull $ARG
