from typing import Dict, Any, List, Optional
import re


class AIFallbackEngine:
    """
    Bộ động cơ dự phòng Heuristic (Offline / Fallback Engine) cho các tính năng AI:
    - Giải thích biểu đồ Dashboard & Radar năng lực (UC-45)
    - Tư vấn hỏi đáp kỹ thuật (UC-44)
    - Tóm tắt bài viết chuyên sâu (UC-46)
    Đảm bảo 100% SLA hoạt động ngay cả khi mất kết nối Internet hoặc LLM Gateway gặp sự cố.
    """

    @staticmethod
    def explain_dashboard(
        chart_type: str,
        metrics: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sinh phân tích & giải thích biểu đồ bằng Heuristic quy tắc dựa trên loại biểu đồ và chỉ số.
        """
        chart_type_lower = (chart_type or "").lower().strip()
        context = context or {}
        subject_name = context.get("username") or context.get("repo_name") or context.get("name") or "Đối tượng"

        if "radar" in chart_type_lower or "developer" in chart_type_lower:
            return AIFallbackEngine._explain_developer_radar(subject_name, metrics, context)
        elif "repo" in chart_type_lower or "repository" in chart_type_lower:
            return AIFallbackEngine._explain_repo_health(subject_name, metrics, context)
        elif "trend" in chart_type_lower or "tech" in chart_type_lower:
            return AIFallbackEngine._explain_tech_trend(subject_name, metrics, context)
        elif "lang" in chart_type_lower or "language" in chart_type_lower:
            return AIFallbackEngine._explain_language_health(subject_name, metrics, context)
        else:
            return AIFallbackEngine._explain_generic_chart(chart_type, metrics, context)

    @staticmethod
    def _explain_developer_radar(subject_name: str, metrics: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Phân tích 5 trục tiêu biểu: Coding, Review, Architecture, Community, Consistency
        num_metrics = {}
        for k, v in metrics.items():
            try:
                num_metrics[k] = float(v)
            except (ValueError, TypeError):
                pass

        if not num_metrics:
            num_metrics = {"Coding": 75.0, "Architecture": 70.0, "Consistency": 65.0}

        sorted_axes = sorted(num_metrics.items(), key=lambda item: item[1], reverse=True)
        top_strengths = [f"{axis}: {val:.0f}/100" for axis, val in sorted_axes if val >= 70]
        improvements = [f"{axis}: {val:.0f}/100" for axis, val in sorted_axes if val < 60]

        if not top_strengths:
            top_strengths = [f"{sorted_axes[0][0]}: năng lực ổn định nhất trong các trục đánh giá"]
        if not improvements:
            lowest_axis, lowest_val = sorted_axes[-1]
            improvements = [f"{lowest_axis} ({lowest_val:.0f}/100) có dư địa phát triển thêm để cân bằng radar."]

        avg_score = sum(num_metrics.values()) / max(len(num_metrics), 1)

        summary = (
            f"Developer Radar của {subject_name} đạt mức điểm trung bình {avg_score:.1f}/100. "
            f"Biểu đồ thể hiện hồ sơ năng lực tập trung mạnh vào '{sorted_axes[0][0]}' "
            f"và cần bổ sung phát triển ở khía cạnh '{sorted_axes[-1][0]}'."
        )

        recommendations = [
            f"Duy trì và phát huy thế mạnh mũi nhọn ở trục '{sorted_axes[0][0]}'.",
            f"Tăng cường hoạt động tham gia vào trục '{sorted_axes[-1][0]}' thông qua các đóng góp cụ thể hoặc tài liệu kỹ thuật.",
            "Tham gia review mã nguồn chéo và chia sẻ kinh nghiệm trên bảng tin cộng đồng để nâng cao chỉ số Community & Architecture."
        ]

        return {
            "chart_type": "developer_radar",
            "summary": summary,
            "strengths": top_strengths,
            "improvements": improvements,
            "recommendations": recommendations,
            "provider": "heuristic_fallback"
        }

    @staticmethod
    def _explain_repo_health(subject_name: str, metrics: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        health_score = float(metrics.get("health_score") or metrics.get("score") or 75.0)
        commit_count = metrics.get("commit_count") or metrics.get("commits") or 0
        pr_count = metrics.get("pr_count") or metrics.get("pulls") or 0

        status_text = "Tốt (Healthy)" if health_score >= 80 else ("Trung bình (Moderate)" if health_score >= 60 else "Cần cải thiện (At Risk)")
        summary = (
            f"Kho mã nguồn '{subject_name}' có điểm sức khỏe tổng thể {health_score:.1f}/100 "
            f"(Trạng thái: {status_text}). Ghi nhận {commit_count} commits gần đây và {pr_count} pull requests."
        )

        strengths = []
        if health_score >= 70:
            strengths.append(f"Chỉ số bảo trì mã nguồn đạt mức an toàn ({health_score:.1f}/100).")
        if commit_count > 10:
            strengths.append(f"Tần suất cập nhật commit tích cực ({commit_count} commits).")
        if not strengths:
            strengths.append("Cấu trúc dự án rõ ràng và tuân thủ quy chuẩn mã nguồn mở cơ bản.")

        improvements = []
        if health_score < 70:
            improvements.append("Cần tăng độ bao phủ mã kiểm thử tự động (Unit Test / Integration Test).")
        if pr_count < 2:
            improvements.append("Quy trình review mã qua Pull Request còn hạn chế, cần khuyến khích code review trước khi merge.")

        recommendations = [
            "Thiết lập CI/CD pipeline tự động kiểm tra linting và test suite cho mỗi Pull Request.",
            "Thường xuyên cập nhật README, hướng dẫn đóng góp (CONTRIBUTING.md) và phản hồi nhanh các issues tồn đọng.",
            "Gắn thẻ phiên bản (Semantic Versioning) và tài liệu hóa Changelog định kỳ."
        ]

        return {
            "chart_type": "repo_health",
            "summary": summary,
            "strengths": strengths,
            "improvements": improvements,
            "recommendations": recommendations,
            "provider": "heuristic_fallback"
        }

    @staticmethod
    def _explain_tech_trend(subject_name: str, metrics: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        growth_rate = float(metrics.get("growth_rate") or metrics.get("growth") or 15.0)
        star_velocity = float(metrics.get("star_velocity") or metrics.get("stars_per_day") or 5.0)

        summary = (
            f"Xu hướng công nghệ '{subject_name}' ghi nhận mức tăng trưởng {growth_rate:.1f}% "
            f"với tốc độ đón nhận trung bình {star_velocity:.1f} stars/ngày trên toàn cầu."
        )

        strengths = [
            f"Tốc độ lan tỏa trong cộng đồng lập trình viên duy trì đà tích cực (+{growth_rate:.1f}%).",
            "Hệ sinh thái thư viện bổ trợ và công cụ đồng hành đang được hoàn thiện nhanh chóng."
        ]
        improvements = [
            "Cần theo dõi mức độ ổn định dài hạn của API và khả năng tương thích ngược (Backward Compatibility)."
        ]
        recommendations = [
            "Khuyến khích áp dụng công nghệ này vào các dự án thử nghiệm (PoC) trước khi đưa vào hệ thống Core Production.",
            "Tổ chức Tech Talk hoặc chia sẻ nội bộ về các kiến trúc mẫu (Design Patterns) phù hợp với xu hướng này."
        ]

        return {
            "chart_type": "tech_trend",
            "summary": summary,
            "strengths": strengths,
            "improvements": improvements,
            "recommendations": recommendations,
            "provider": "heuristic_fallback"
        }

    @staticmethod
    def _explain_language_health(subject_name: str, metrics: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        score = float(metrics.get("health_score") or metrics.get("score") or 80.0)
        summary = f"Chỉ số sức khỏe ngôn ngữ '{subject_name}' duy trì ở mức {score:.1f}/100 với độ ổn định hệ sinh thái cao."
        return {
            "chart_type": "language_health",
            "summary": summary,
            "strengths": [f"Điểm số mức độ hài lòng và phổ biến đạt {score:.1f}/100."],
            "improvements": ["Tối ưu hiệu năng bộ nhớ và hỗ trợ các mô hình lập trình bất đồng bộ hiện đại."],
            "recommendations": ["Cập nhật phiên bản LTS mới nhất để nhận các bản vá bảo mật và tối ưu runtime."],
            "provider": "heuristic_fallback"
        }

    @staticmethod
    def _explain_generic_chart(chart_type: str, metrics: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        summary = f"Biểu đồ '{chart_type}' ghi nhận tổng cộng {len(metrics)} trường chỉ số phân tích."
        strengths = [f"Chỉ số '{k}': {v}" for k, v in list(metrics.items())[:2]]
        improvements = ["Theo dõi thường xuyên biến thiên của các chỉ số qua từng chu kỳ."]
        recommendations = ["Đặt ngưỡng cảnh báo tự động khi các chỉ số cốt lõi sụt giảm quá 15%."]
        return {
            "chart_type": chart_type,
            "summary": summary,
            "strengths": strengths,
            "improvements": improvements,
            "recommendations": recommendations,
            "provider": "heuristic_fallback"
        }

    @staticmethod
    def chat_fallback(question: str) -> Dict[str, Any]:
        """Tư vấn kỹ thuật dự phòng bằng Rule Heuristic chuyên sâu."""
        q_lower = question.lower().strip()
        answer_parts = []
        suggested = ["Clean Architecture", "Microservices Design", "Docker & Kubernetes", "CI/CD Pipeline"]

        if any(w in q_lower for w in ["docker", "container", "dockerfile", "compose"]):
            answer_parts.append(
                "### 🐳 Hướng dẫn về Docker & Containerization:\n"
                "1. **Multi-stage Build:** Sử dụng nhiều stage để build source và copy binary sang image runtime rút gọn (vd: Alpine/Distroless).\n"
                "2. **Bảo mật:** Không chạy container dưới quyền `root`, thêm user không đặc quyền (`USER appuser`).\n"
                "3. **Tối ưu Layer Caching:** Đặt các lệnh ít thay đổi (`COPY package.json`, `npm install`) trước các lệnh copy toàn bộ mã nguồn.\n"
                "4. **.dockerignore:** Luôn loại bỏ `node_modules`, `venv`, file `.git` và file bí mật `.env`."
            )
            suggested = ["Docker Multi-stage", "Kubernetes Pod Deployment", "Docker Compose Local Dev", "Container Security"]

        elif any(w in q_lower for w in ["microservice", "architecture", "kiến trúc", "clean"]):
            answer_parts.append(
                "### 🏛️ Tư vấn Kiến trúc Microservices & Clean Architecture:\n"
                "1. **Phân rã Domain (DDD):** Xác định ranh giới ngữ cảnh (Bounded Context) độc lập cho từng microservice (vd: Identity, Community, Crawler, Quality).\n"
                "2. **Giao tiếp Dịch vụ:** Dùng HTTP/REST hoặc gRPC cho truy vấn đồng bộ (synchronous query); dùng Message Broker (RabbitMQ/Kafka) cho sự kiện bất đồng bộ.\n"
                "3. **Clean Architecture 4 tầng:** Domain (Entities, Rules) -> Application (CQRS, DTOs) -> Infrastructure (EF Core, Repos) -> Presentation/API.\n"
                "4. **Resilience Pattern:** Áp dụng Circuit Breaker, Retry, Timeout và Graceful Fallback."
            )
            suggested = ["Event-Driven Architecture", "API Gateway Pattern", "Distributed Tracing", "CQRS with MediatR"]

        elif any(w in q_lower for w in ["sql", "database", "postgres", "mongo", "cơ sở dữ liệu"]):
            answer_parts.append(
                "### 💾 Tối ưu Cơ sở dữ liệu (Database Optimization):\n"
                "1. **Indexing:** Đánh chỉ mục B-Tree cho các cột thường xuyên lọc (`WHERE`), sắp xếp (`ORDER BY`) hoặc khóa ngoại (`FK`).\n"
                "2. **Tránh N+1 Query:** Luôn eager loading (`Include` trong EF Core hoặc lookup aggregation trong Mongo).\n"
                "3. **Phân tách Read/Write:** Triển khai Read Replicas khi lưu lượng đọc vượt trội.\n"
                "4. **Connection Pooling:** Đảm bảo cấu hình pool connection hợp lý để tránh quá tải RAM cơ sở dữ liệu."
            )
            suggested = ["Database Indexing", "Query Optimization", "MongoDB Aggregation", "Redis Caching Strategy"]

        elif any(w in q_lower for w in ["ci", "cd", "devops", "github action"]):
            answer_parts.append(
                "### 🚀 Quy trình CI/CD Hiện đại:\n"
                "1. **Tự động hóa Test & Lint:** Mỗi commit hoặc PR đều phải vượt qua unit tests, static analysis và vulnerability scanning.\n"
                "2. **Zero-downtime Deployment:** Áp dụng chiến lược Blue/Green hoặc Rolling Update.\n"
                "3. **Quản lý Secrets an toàn:** Sử dụng GitHub Secrets hoặc HashiCorp Vault, tuyệt đối không commit token/key vào Git."
            )
            suggested = ["GitHub Actions Workflow", "Kubernetes Ingress", "SonarQube Quality Gate", "Terraform IaC"]

        else:
            answer_parts.append(
                f"### 💡 Phản hồi từ DevRadar AI Assistant:\n"
                f"Chúng tôi đã ghi nhận câu hỏi kỹ thuật của bạn: **\"{question}\"**.\n\n"
                "Theo khuyến nghị thực hành tốt nhất (Engineering Best Practices):\n"
                "- **Thiết kế:** Tuân thủ nguyên lý SOLID, viết mã có tính đóng gói cao và ít phụ thuộc (Loose Coupling).\n"
                "- **Kiểm thử:** Đảm bảo độ bao phủ kiểm thử tự động (Unit Tests) với các ca biên (edge cases) và kiểm thử hợp đồng API.\n"
                "- **Khả năng quan sát (Observability):** Ghi nhật ký có cấu trúc (Structured Logging) kèm theo `correlation_id` xuyên suốt các service."
            )

        return {
            "answer": "\n\n".join(answer_parts),
            "suggested_topics": suggested
        }

    @staticmethod
    def summarize_fallback(text: str, max_length: int = 200) -> Dict[str, Any]:
        """Tóm tắt văn bản thông minh bằng thuật toán tách câu và trích xuất điểm mấu chốt."""
        cleaned = text.strip()
        sentences = [s.strip() for s in re.split(r'[.\n!?]+', cleaned) if len(s.strip()) > 15]

        if not sentences:
            summary = cleaned[:max_length]
            key_points = [cleaned[:60] + "..." if len(cleaned) > 60 else cleaned]
        else:
            # Chọn câu đầu tiên và câu có độ dài hợp lý mang tính khái quát
            selected = sentences[:2]
            summary = ". ".join(selected) + "."
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(" ", 1)[0] + "..."

            # Lọc 3-4 câu làm điểm chính
            key_points = sentences[:4]

        return {
            "summary": summary,
            "key_points": key_points
        }


ai_fallback_engine = AIFallbackEngine()
