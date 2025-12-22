def diff_blocks(old_blocks, new_blocks):
    old_map = {b["sequence_no"]: b for b in old_blocks}
    new_map = {b["sequence_no"]: b for b in new_blocks}

    changes = []

    for seq, new in new_map.items():
        if seq not in old_map:
            changes.append({"type": "ADDED", "sequence_no": seq, "new": new})
        else:
            old = old_map[seq]
            if old["text"] != new["text"] or old["styles"] != new["styles"]:
                changes.append({
                    "type": "MODIFIED",
                    "sequence_no": seq,
                    "old": old,
                    "new": new
                })

    for seq in old_map:
        if seq not in new_map:
            changes.append({"type": "REMOVED", "sequence_no": seq})

    return changes
