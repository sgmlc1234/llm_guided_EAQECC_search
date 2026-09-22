"""Audit the prospective eight-block cohort offline, including its missing response."""
import argparse
import ast
import itertools
import json
from pathlib import Path
from statistics import mean
import sys

from common import ROOT, code_hash, expected_prompt, rank_key, ranked, read, sha


def audit(bundle):
    sys.path.insert(0, str(bundle / 'runtime'))
    from independent_verify import verify
    from target_driver import inspect_target_code
    from target_execution import target_seed
    p = read(bundle / 'protocol.json')
    cohorts = read(bundle / 'cohorts.json')
    chosen = read(bundle / 'selected_programs.json')
    held = read(bundle / 'heldout_results.json')
    missing = read(bundle / 'unavailable_proposals.json')
    manifest = bundle / 'MANIFEST.sha256.json'
    if manifest.exists():
        for name, digest in read(manifest).items():
            assert sha(bundle / name) == digest, name
    for name, digest in p['input_hashes'].items():
        assert sha(bundle / name) == digest, name
    if 'origin_input_hashes' in p:
        changed = {name for name, digest in p['input_hashes'].items()
                   if digest != p['origin_input_hashes'][name]}
        assert changed <= {f'feasibility/n{n}.check.json' for n in (7, 9, 11, 13, 15)}
    assert len(cohorts) == len(held) == 8
    accepted = 0
    for block, arms in cohorts.items():
        for arm, pool in arms.items():
            expected_count = 8 - sum(key.startswith(f'b{int(block):02d}_{arm}_') for key in missing)
            assert len(pool) == expected_count
            for i, item in enumerate(pool[1:], 1):
                folder = bundle / 'candidates' / item['id']
                assert (folder / 'program.py').read_text() == item['code']
                assert code_hash(item['code']) == item['evaluation']['code_sha256']
                inspect_target_code(item['code'])
                prior = pool[:i]
                parent = pool[0] if arm == 'independent' else ranked(prior)[0]
                last = None if arm == 'independent' or item['generation'] == 0 else prior[-1]
                request = read(folder / 'request.json')
                assert request['contents'][0]['parts'][0]['text'] == expected_prompt(bundle, p, parent, last)
                assert request['generationConfig']['seed'] == p['model_seed_base'] + int(block)*100 + item['generation']
                assert read(folder / 'parentage.json') == dict(parent=parent['id'], latest=last['id'] if last else None)
                response = read(folder / 'response.json')
                parts = response['candidates'][0]['content']['parts']
                returned = json.loads(''.join(x.get('text', '') for x in parts if not x.get('thought')))['code']
                assert returned == item['code']
                accepted += 1
            short = ranked(pool)[:3]
            def key(item):
                value = read(bundle / 'validation' / code_hash(item['code']) / 'evaluation.json')
                return value['mean_utility'], value['success_fraction'], value['mean_distance_ratio'], rank_key(item)
            assert max(short, key=key)['id'] == chosen[block][arm]['program_id']
            for split in ('test', 'transfer'):
                assert held[block][arm][split] == read(bundle / split / chosen[block][arm]['code_sha256'] / 'evaluation.json')
    assert accepted == 111 and accepted + len(missing) == 112
    evaluations = 0
    for path in bundle.rglob('evaluation.json'):
        value = read(path)
        if 'cases' not in value:
            continue
        parts = path.relative_to(bundle).parts
        split = next((s for s in ('transfer', 'test', 'validation') if s in parts), 'train')
        lengths = p['transfer_lengths'] if split == 'transfer' else p['train_lengths']
        expected = {(n, target_seed(seed, read(bundle / 'feasibility' / f'target_n{n}.json')[0]))
                    for n in lengths for seed in p[split + '_seeds']}
        assert {(c['target']['n'], c['seed']) for c in value['cases']} == expected, path
        assert len(value['cases']) == len(expected)
        for case in value['cases']:
            assert case['allocated_evals'] == p[split + '_budget']
            assert not case['protected_initialization']
            assert case['phase_evals']['initialization'] == 0
            calls = case['n_evals']
            assert 0 <= calls <= case['allocated_evals']
            utility = 1 - calls/case['allocated_evals'] if case['closed'] and not case.get('error') else 0
            assert abs(case['utility'] - utility) < 1e-12
        assert abs(value['mean_utility'] - mean(c['utility'] for c in value['cases'])) < 1e-12
        assert abs(value['success_fraction'] - mean(c['closed'] for c in value['cases'])) < 1e-12
        evaluations += len(value['cases'])
    checked = 0
    for path in bundle.rglob('*.witness.json'):
        t = read(path)['target']
        verify(path, [t[k] for k in ('n', 'k', 'd', 'c')])
        checked += 1
    # Static inventory supports, but does not replace, the recorded source review.
    selected = []
    for arms in chosen.values():
        for arm, item in arms.items():
            tree = ast.parse(item['code'])
            helpers = sorted({ast.unparse(n.func) for n in ast.walk(tree)
                              if isinstance(n, ast.Call) and ast.unparse(n.func).startswith('E.')})
            assert set(helpers) <= {'E.evaluate', 'E.nullspace', 'E._J', 'E.gf2_basis'}
            selected.append({'id': item['program_id'], 'arm': arm, 'sha256': item['code_sha256'], 'helpers': helpers})
    differences = [v['evolution']['test']['mean_utility'] - v['independent']['test']['mean_utility'] for v in held.values()]
    observed = mean(differences)
    probability = sum(abs(mean(s*x for s, x in zip(signs, differences))) >= abs(observed)-1e-12
                      for signs in itertools.product((-1, 1), repeat=8))/256
    analysis = read(bundle / 'replication_analysis.json')
    assert abs(observed-analysis['primary_mean_auc_difference']) < 1e-12
    assert probability == analysis['descriptive_two_sided_sign_flip_p']
    return {'status': 'PASS', 'accepted_proposals': accepted, 'unavailable_slots': len(missing),
            'generation_blocks': 8, 'selected_programs': selected,
            'distinct_selected_sources': len({x['sha256'] for x in selected}),
            'evaluation_records': evaluations, 'code_records_independently_rechecked': checked,
            'mean_paired_auc_difference': observed, 'positive_blocks': sum(x > 0 for x in differences),
            'descriptive_sign_flip_p': probability,
            'source_review_scope': 'See SOURCE_REVIEW.md for manual review; the static helper inventory alone is not a proof of compliance.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', type=Path, default=ROOT / 'experiments/hitl_replication')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    result = audit(args.bundle.resolve())
    output = json.dumps(result, indent=2) + '\n'
    if args.out:
        args.out.write_text(output)
    print(output)
