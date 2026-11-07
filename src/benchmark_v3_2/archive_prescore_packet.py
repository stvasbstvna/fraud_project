"""One-time documented correction before any API source validation."""
from .core import *
def archive():
    if list((DATA/'review').rglob('*.request.json')):raise ValueError('Cannot amend source packet after calls')
    paths=['source/family_screen.csv','source/family_edges.csv','source/review_candidates.csv','source/outbound_packet.json','provenance/outbound_authorization.json']
    old=[]
    for rel in paths:
        p=DATA/rel
        if p.exists():
            target=DATA/'source/history/prescore_packet_v1'/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():raise ValueError('Archive exists')
            old.append({'path':rel,'sha256':file_sha(p)})
            p.rename(target)
    immutable_json(DATA/'source/history/prescore_packet_v1/manifest.json',{'timestamp':now(),'files':old,'status':'SUPERSEDED_BEFORE_API_OR_SCORING','reason':'Upstream NUS native id18088 belongs to two different texts; exclude both ambiguous rows. Earlier dict-based packet collapsed one id. Original prepared outbound packet retained; no API call used it.'})
    immutable_text(DOCS/'CORRECTION_20261107_PRE_SOURCE_API.md','# Pre-source-API correction\n\nThe source-expansion export initially contained709 rows/708 native IDs. Native NUS id18088 had two different personal-chat texts. Both were excluded, leaving707 unique candidate IDs. Source exporter corrected its new CSV before receiving the parent stop message; the initial prepared packet, candidate CSV and family diagnostics are preserved under data/benchmark_v3_2/source/history/prescore_packet_v1. No research API call or detector scoring used that packet. Regenerate source packet from corrected707-candidate file. No v3 result or model changed; no v3.2 scientific claim changed.\n')
if __name__=='__main__':archive()
