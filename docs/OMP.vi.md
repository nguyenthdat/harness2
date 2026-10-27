# Hướng dẫn tối ưu OMP profile

[English](OMP.md) | Tiếng Việt

Hướng dẫn này chạy Harness² với [OMP executor](SETUP.md#omp-executor) trên
[JobBench](BENCHMARKS.md#jobbench) (OMP cũng hỗ trợ [WorkBuddy-Bench](BENCHMARKS.md#workbuddy-bench) và LAB),
dùng model DeepSeek cho mọi vai, rồi đưa những gì học được vào OMP profile của bạn. Các lệnh chạy từ thư mục gốc của
repo. Recursion budget và quy tắc resume xem ở
[experiment guide](EXPERIMENTS.md).

## Harness² dùng OMP như thế nào

Với mỗi task, Harness² chạy các rollout tham chiếu với harness hiện tại, nhờ
improver đề xuất các bản sửa, chạy thử từng bản sửa bằng một rollout riêng, gộp
thành một harness đã tinh chỉnh dựa trên bằng chứng, rồi chọn harness cuối cùng
mà không nhìn rubric chấm điểm. Sau đó bước reflection lưu harness được chọn
cùng một bài học có bằng chứng vào library của domain; các task sau trong cùng
domain sẽ đọc library này.

Bản sửa thuộc một trong hai hướng:

| Hướng | Phụ trách |
|---|---|
| INV (invariant) | Agent làm việc thế nào: quy trình, dùng tool, kiểm tra, hoàn tất |
| DOM (domain) | Người làm nghề trong lĩnh vực của task biết những gì |

Mỗi task tốn `4k` rollout executor và `3k` phiên improver, nên `--k 1` nghĩa là
4 rollout và 3 phiên improver.

Mỗi rollout là một tiến trình `omp --profile harness2 -p --mode json` trong một
workspace mới của task. Overlay settings riêng cho từng lần chạy tắt advisor,
memory, recap và autolearn, khoá mọi model role và subagent vào model executor,
và tự duyệt mọi tool call. Harness² không bao giờ đọc hay ghi profile của bạn;
việc đưa kết quả vào đó là bước thủ công ở mục "7. Đưa kết quả vào profile".

Harness là tập file mà Harness² được phép sửa. Chúng nằm ở gốc workspace, nơi
OMP tự tìm thấy:

| Đường dẫn | Vai trò | Khi nào nằm trong context |
|---|---|---|
| `AGENTS.md` | Vai trò, quy trình, rule thường trực | Mọi lượt; tối đa 8.000 ký tự |
| `.omp/skills/<name>/SKILL.md` | Workflow dùng lại được; bắt buộc có frontmatter `description:` | Tên và mô tả có sẵn từ đầu, phần thân đọc khi cần qua `skill://<name>`; chỉ được mở khi `AGENTS.md` nêu tên nó trong một dòng trigger |
| `sub_agents/<name>/AGENT.md` | Agent được giao việc | Được cài thành task agent `.omp/agents/<name>.md`; chạy trong context riêng |
| `scripts/<name>.py` | Script phụ trợ cho kết quả xác định | Khi agent chạy `python3 scripts/<name>.py` |
| `.omp/extensions/<name>.ts` | Handler bên trong vòng gọi tool (`tool_call`, `tool_result`, `session_stop`) | Luôn được nạp |

JobBench bắt đầu mọi task từ một `AGENTS.md` chỉ có hai dòng
(`third_party/jb_runner/codex_base_harness/AGENTS.md`).

## Yêu cầu

- macOS hoặc Linux, có `git`, `npm`, Node.js 20 trở lên và
  [uv](https://docs.astral.sh/uv/getting-started/installation/). LAB cần thêm
  Pandoc và Poppler (`brew install pandoc poppler` trên macOS); JobBench thì không. WorkBuddy cần Docker.
- `omp` có trong `PATH`, hoặc đặt `HARNESS2_OMP_BIN` trỏ tới nó. Setup không cài
  và không pin OMP.
- Một API key DeepSeek.
- Khoảng 3,5 GB ổ đĩa cho dependency của JobBench trong `dependencies/`.

Các bước 1 đến 4 đã được kiểm chứng trên macOS (arm64) với omp 18.12.5.

## 1. Cài Harness²

```bash
uv venv --python 3.12 .venv    # thêm --clear để thay .venv đang có
source .venv/bin/activate
uv pip install -e '.[render]'
harness2-demo --output runs/demo --k 2
```

Demo không cần credential và kết thúc bằng `2 tasks completed; 0 failed`.

## 2. Cài JobBench cho OMP

```bash
harness2-setup jb --substrate omp --dry-run    # xem trước kế hoạch
harness2-setup jb --substrate omp
```

Setup clone bản OpenCode đã pin mà improver chạy trên đó, cài Bun 1.3.11 vào
`dependencies/tools`, clone và patch `job-bench-eval` kèm môi trường Python 3.12
riêng, tải dataset (65 task thuộc 35 nghề), rồi in ra thư mục của profile
`harness2`.

## 3. Cấu hình DeepSeek

OMP và bản OpenCode đã pin đều có sẵn provider `deepseek` đọc
`DEEPSEEK_API_KEY`, nên profile không cần `models.yml`. Liệt kê các model ID mà
key của bạn dùng được:

```bash
curl -s https://api.deepseek.com/models -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

Tạo `.env` ở gốc repo với các model ID lấy từ danh sách đó, rồi giới hạn quyền
đọc bằng `chmod 600 .env`:

```bash
DEEPSEEK_API_KEY=sk-...
HARNESS2_OMP_MODEL=deepseek/deepseek-v4-pro
HARNESS2_OMP_PROFILE=harness2
HARNESS2_SOLVER_MODEL=deepseek/deepseek-v4-pro
HARNESS2_IMPROVER_MODEL=deepseek/deepseek-v4-pro
HARNESS2_JUDGE_MODEL=deepseek-v4-pro
HARNESS2_JUDGE_BASE_URL=https://api.deepseek.com
HARNESS2_JUDGE_API_KEY=sk-...
```

| Biến | Dùng cho |
|---|---|
| `HARNESS2_OMP_MODEL` | Rollout của executor |
| `HARNESS2_OMP_PROFILE` | Profile mà rollout chạy dưới đó; mặc định là `harness2` |
| `HARNESS2_SOLVER_MODEL` | Bắt buộc với mọi lệnh, theo dạng `provider/model` của OpenCode; là giá trị mặc định cho model executor và improver |
| `HARNESS2_IMPROVER_MODEL` | Các phiên improver: đề xuất, gộp, chọn, reflection |
| `HARNESS2_JUDGE_MODEL`, `HARNESS2_JUDGE_BASE_URL`, `HARNESS2_JUDGE_API_KEY` | `harness2-judge`, qua judge client tương thích OpenAI của JobBench |
| `HARNESS2_IMPROVER_CHANNEL` | Channel improver: `opencode` (mặc định), `claude_cli`, hoặc `omp` |
| `HARNESS2_IMPROVER_OMP_PROFILE` | Profile dùng khi `HARNESS2_IMPROVER_CHANNEL=omp`; mặc định là `HARNESS2_OMP_PROFILE` hoặc `default` |

- Harness² tự nạp `.env`, và biến trong shell được ưu tiên hơn. Nó không expand
  `$VAR`, nên key của judge phải ghi lại lần nữa; khi đổi key thì sửa cả hai
  dòng.
- `deepseek-flash` thay được `deepseek-v4-pro` ở mọi vai. Model được ghi lại
  cùng run, nên hãy chọn trước lần chạy đầu tiên.
- Mặc định, improver chạy với thư mục data OpenCode riêng và không có các biến
  `ANTHROPIC_*`, nên login của OpenCode và API key Anthropic không tới được nó.
  Khi đặt `HARNESS2_IMPROVER_CHANNEL=omp`, các phiên improver thích ứng đệ quy
  (đề xuất, gộp, chọn) sẽ chạy trực tiếp qua `omp` sử dụng `HARNESS2_IMPROVER_OMP_PROFILE`.
  Provider nào mà cả OMP lẫn OpenCode đều đọc từ một biến API key thì thay được
  DeepSeek theo cùng cách, với judge dùng một endpoint tương thích OpenAI; đường
  Vertex AI xem ở [Models and credentials](SETUP.md#models-and-credentials).

## 4. Kiểm tra trước khi tốn tiền

```bash
harness2-check --bench jb --substrate omp
```

Bản cài sẵn sàng sẽ in `Ready: jb/omp; 65 tasks`. Lệnh check xác nhận model
executor resolve được dưới profile `harness2` mà không gọi model. Muốn tự kiểm
tra bằng tay thì nạp `.env` trước, vì `omp` không đọc file này:

```bash
set -a; . ./.env; set +a
omp --profile harness2 models deepseek/deepseek-v4-pro --json
curl -s https://api.deepseek.com/user/balance -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

`omp models` liệt kê một provider ngay khi credential của nó được cấu hình, mà
không kiểm tra credential đó: ví dụ credential `~/.aws` đã hỏng vẫn làm model
Bedrock hiện ra. Lệnh xem balance chứng minh key hoạt động và không tốn tiền.

## 5. Chạy

Mỗi thí nghiệm dùng một thư mục output riêng. Run directory của nó ghi lại
model executor, improver và judge, endpoint của judge, version `omp` và profile,
cùng cách chọn task (`--only-domains`, `--max-tasks`, `--seed`); lệnh sau với
giá trị khác sẽ bị từ chối. Giữ biến này được export cho cả lệnh judge và
report.

```bash
export HARNESS2_RUNS_DIR=runs/jb-omp-deepseek

# Xem trước danh sách task; không gọi model
harness2 --bench jb --substrate omp --k 1 --mode parallel \
  --only-domains computer_and_information_research_scientists --max-tasks 1 --dry-run

# Refine; một rollout có thể kéo dài tới 60 phút, nên chạy trong tmux hoặc terminal riêng
harness2 --bench jb --substrate omp --k 1 --mode parallel \
  --only-domains computer_and_information_research_scientists --max-tasks 1

# Chấm harness được chọn, rồi chấm harness gốc, rồi xem report
harness2-judge  --bench jb --substrate omp --k 1 --mode parallel
harness2-judge  --bench jb --substrate omp --k 1 --mode parallel --bases
harness2-report --bench jb --substrate omp --k 1 --mode parallel
```

`SUBSTRATE=omp bash scripts/run_jobbench.sh --only-domains ... --max-tasks 1`
chạy check, refine, chấm điểm và report trong một lệnh, không có `--bases`.
Chạy lại đúng lệnh cũ để resume.

`--max-tasks` giới hạn số task trên mỗi domain, còn `--workers N` chạy `N`
domain cùng lúc. Các task trong một domain luôn chạy theo thứ tự, task sau đọc
các entry library của những task trước, nên chạy trọn một domain giúp task sau
tận dụng bài học của task trước. Các domain dưới đây gần với công việc phần mềm
nhất: task của chúng kết hợp dữ liệu CSV, XLSX, SQLite và Markdown bằng phân
tích có viết script, rồi xuất ra tài liệu và bảng.

| Domain | Số task |
|---|---|
| `computer_and_information_research_scientists` | 2 |
| `statisticians` | 3 |
| `web_administrators` | 1 |

`--dry-run` không kèm `--only-domains` sẽ liệt kê mọi domain.

## 6. Đọc kết quả

Các đường dẫn dưới đây nằm trong `$HARNESS2_RUNS_DIR/jb/`, ứng với
`--k 1 --mode parallel` (namespace `jb-omp-agg1`; chế độ sequential dùng `seq`
thay cho `agg`).

| Đường dẫn | Nội dung |
|---|---|
| `adapt/jb-omp-agg1/<domain>__<task>/summary.json` | `selections.agg.chosen_label` là tên harness được chọn; `chosen_tree_is_base: true` nghĩa là không bản sửa nào được giữ lại |
| `adapt/jb-omp-agg1/<domain>__<task>/harnesses/` | `base`, hai ứng viên `inv1` và `dom1`, và bản gộp `agg1` |
| `adapt/jb-omp-agg1/judged.json`, `base_judged.json` | Điểm của harness được chọn và của harness gốc |
| `library/jb/k1-omp/agg/<domain>/INDEX.md` | Mục lục library của domain |
| `library/jb/k1-omp/agg/<domain>/harnesses/<domain>__<task>/` | `harness/` là cây harness được chọn, `EXPERIENCE.md` ghi lý do chọn, tác dụng của từng bản sửa, và bài học kèm cue, evidence, confidence |
| `dataset/<domain>/<task>/model_output/`, `model_traj/` | Deliverable của từng rollout, cùng event stream, stderr, overlay settings và OMP session của nó |

Xem một task đã sửa gì:

```bash
T=$HARNESS2_RUNS_DIR/jb/adapt/jb-omp-agg1/computer_and_information_research_scientists__task1
grep chosen_label "$T/summary.json"
diff -ru "$T/harnesses/base" "$T/harnesses/agg1"    # thay agg1 bằng label được chọn
```

## 7. Đưa kết quả vào profile

Profile giữ các thành phần cấp user trong `~/.omp/profiles/<profile>/agent/`,
ví dụ `~/.omp/profiles/coder/agent/`. Chuyển từng thành phần bằng tay:

| Harness được chọn | Vị trí trong profile | Ghi chú |
|---|---|---|
| Một rule trong `AGENTS.md` | `AGENTS.md` | Gộp rule vào; không bao giờ thay cả file |
| `.omp/skills/<name>/` | `skills/<name>/` | Mang theo cả dòng trigger của skill vào `AGENTS.md` |
| `sub_agents/<name>/AGENT.md` | `agents/<name>.md` | Frontmatter phải có `name: <name>`; OMP bỏ qua agent thiếu dòng này |
| `scripts/<name>.py` | `skills/<skill>/scripts/<name>.py` | Profile không có `scripts/` theo workspace; sửa đường dẫn trong rule hoặc skill gọi nó |
| `.omp/extensions/<name>.ts` | `extensions/<name>.ts` | Được nạp ở mọi phiên; đọc kỹ trước khi chép |

RE profile của repository giữ sáu skill với tên chuẩn trong `profiles/re/agent/skills/`:
[c-to-rust-port](../profiles/re/agent/skills/c-to-rust-port/SKILL.md),
[python-coding](../profiles/re/agent/skills/python-coding/SKILL.md),
[repository-change](../profiles/re/agent/skills/repository-change/SKILL.md),
[reverse-engineering](../profiles/re/agent/skills/reverse-engineering/SKILL.md),
[rust-coding](../profiles/re/agent/skills/rust-coding/SKILL.md) và
[static-artifact-analysis](../profiles/re/agent/skills/static-artifact-analysis/SKILL.md).
Tên thư mục trùng với trường YAML `name`; đọc skill qua `skill://<name>`.

```bash
E=$HARNESS2_RUNS_DIR/jb/library/jb/k1-omp/agg/statisticians/harnesses/statisticians__task1
P=~/.omp/profiles/coder/agent
cat "$E/EXPERIENCE.md"
cp -R "$E/harness/.omp/skills/<name>" "$P/skills/"
```

Nên chuyển gì:

- Bản sửa INV (quy trình, dùng tool, kiểm tra) có bằng chứng trong
  `EXPERIENCE.md`. Bỏ lại bản sửa DOM: chúng chứa kiến thức của riêng một nghề.
- Đừng chuyển extension từ chối kết thúc khi một file chưa tồn tại, ví dụ
  deliverable trong `output/`: trong profile tương tác, nó chặn mọi phiên không
  ghi ra file đó.
- Bài học được học với model executor trên một `AGENTS.md` hai dòng. Profile
  chạy model khác hoặc có `AGENTS.md` dài có thể đã có bài học đó hoặc mâu thuẫn
  với nó; kiểm tra trước khi gộp, và dùng profile vài phiên thật sau đó.
- Muốn thử một harness mà không đụng tới profile, hãy cài nó vào một bản sao
  nháp của một project theo đúng cách Harness² đã rollout: `AGENTS.md`,
  `scripts/` và `.omp/` ở gốc, mỗi `sub_agents/<name>/AGENT.md` chuyển thành
  `.omp/agents/<name>.md`.

## Lưu ý

- Giữ `HARNESS2_OMP_PROFILE` ở một profile chuyên dụng. Overlay không ngăn MCP
  server hay extension của profile được nạp, và rollout tự duyệt mọi tool call
  khi không ai theo dõi; với profile dùng hằng ngày có MCP điều khiển desktop
  hoặc ghi note, rollout có thể dùng chúng.
- JobBench công khai `RUBRICS.json` của từng task, và rollout có thể tải về.
  Chặn các host liệt kê ở [Web access](EXPERIMENTS.md#web-access) ở mức mạng
  trong lúc chạy.
- Khi DeepSeek vừa là executor vừa là judge, judge chấm bài của chính model đó.
  DeepSeek nhận input ảnh nhưng trả lời là không nhìn thấy ảnh, nên rubric cần
  xem biểu đồ sẽ bị chấm mà không thấy biểu đồ.
- `omp update` làm thay đổi runtime đã ghi trong run. Chạy xong rồi mới update,
  sau đó dùng `HARNESS2_RUNS_DIR` mới.
